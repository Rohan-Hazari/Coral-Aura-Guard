from __future__ import annotations

import json
import os
import logging
import asyncio
from typing import List, Optional

from pydantic_ai import Agent, ModelSettings
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.usage import UsageLimits
from pydantic_ai.exceptions import UnexpectedModelBehavior, UsageLimitExceeded

# Default to Gemini Flash as requested
DEFAULT_MODEL = "google:gemini-1.5-flash"
MAX_OUTPUT_TOKENS = 32000 
GLOBAL_TIMEOUT = 120 # 2 minutes timeout for all agent operations

SYSTEM_PROMPT = """You are a Pydantic AI SRE assistant for Aura Guard.

Operating principles:
- Treat CloudWatch, GitHub, OSV, and Linear as evidence sources. Use Coral MCP tools before making factual claims.
- **Incremental Discovery**: Prefer narrow SQL queries with LIMIT clauses. Avoid broad scans.
- **GitHub Repositories**: Use `github.repositories` and filter by `owner__login` when searching for repositories belonging to a specific user (e.g., 'Rohan-Hazari').
- **GitHub Pull Requests**: The `github.pulls` table REQUIRES both `owner` and `repo` filters in the WHERE clause. You cannot query pulls globally.
- **GitHub Content**: When reading files from GitHub, ALWAYS select the `content_text` column from the `github.contents` table to get decoded UTF-8 text. Avoid the raw `content` column which is base64 encoded.
- **CloudWatch Logs**: Use `cloudwatch_logs.log_events`. You MUST filter by `log_group_name` or `log_group_identifier`.
- Distinguish observations from hypotheses. Tag hypotheses with confidence (High/Medium/Low).
- Cite sources: Prefix evidence with [Source Name] [Identifier]. 
- You are READ-ONLY. Do not claim to have performed actions.

You handle three specific types of investigations. Use the ## headers defined in the task below for your final report.

1. **Incident Triage (Chain of Thought)**
   - Step 1: Query `cloudwatch_logs.log_events` for errors related to the service. Get exact timestamps. Note: This table REQUIRES a `log_group_name` filter.
   - Step 2: Query `github.commits` within a **3-day window** preceding the earliest error.
   - Step 3: Query `linear.issues` to correlate the commit message to intent.
   - **Report Structure**: Use ## Summary, ## Evidence, ## Likely cause (Confidence), ## Blast radius, ## What changed (3-day window), ## Mitigation, ## Sources.

2. **Supply Chain Audit (Delta Scan)**
   - Step 1: Query `github.contents` to read `package.json`, `Cargo.toml`, or `requirements.txt`.
   - Step 2: Extract dependencies and join them with `osv.query_by_version` to find vulnerabilities.
   - Step 3: If a PR is specified, compare `github.pulls` base and head SHAs to find ONLY *newly introduced* vulnerabilities.
   - Step 4: Query `linear.issues` using dependency names to find related security tickets or planned upgrades.
   - **Report Structure**: Use ## Audit Summary, ## Vulnerabilities Found (Table), ## Linear Correlation, ## Risk Assessment, ## Remediation, ## Sources.

3. **Blast Radius Evaluation (Impact Analysis)**
   - Step 1: Query `github.search_code` to find repositories importing a specific file/package.
   - Step 2: Query `github.pulls` to see if those downstream repos have active PRs at risk.
   - Step 3: Query `linear.issues` for affected repos to find planned maintenance or feature work.
   - **Report Structure**: Use ## Impact Summary, ## Affected Downstream Repositories, ## Active Pull Requests at Risk, ## Linear Planning Context, ## Notification Plan, ## Sources.

Tool Usage:
- Your primary tool is `sql`. Use it to query any table in the Coral database.
- If you don't know which table to use, use `list_catalog` or `search_catalog`.
- IMPORTANT: Always use the exact tool name `sql`. Never use `mcp_coral_sql`.
- CRITICAL: When using the `sql` tool, provide the raw SQL string as the `sql` parameter. Do NOT use markdown backticks (```sql), and do NOT add CLI flags like `--format json` to the SQL query.
"""

import traceback
import time
from datetime import datetime

logger = logging.getLogger("aura-guard.agent")

class AuraGuardAgent:
    _coral_server: Optional[MCPServerStdio] = None

    def __init__(
        self,
        model: str | None = None,
        max_tool_rounds: int = 8, # Keep agent loops bounded for interactive endpoints
    ):
        self.model = model or os.getenv("MODEL_NAME") or DEFAULT_MODEL
        self.max_tool_rounds = max_tool_rounds
        self.coral_bin = os.getenv("CORAL_BIN", "coral")
        
        # Map generic MODEL_API_KEY to provider-specific keys for Pydantic AI
        api_key = os.getenv("MODEL_API_KEY")
        provider = os.getenv("MODEL_PROVIDER", "").lower()
        
        if api_key:
            if provider == "google" or "google" in self.model.lower() or "gemini" in self.model.lower():
                os.environ["GOOGLE_API_KEY"] = api_key
            elif provider == "openai" or "openai" in self.model.lower() or "gpt" in self.model.lower():
                os.environ["OPENAI_API_KEY"] = api_key

    @staticmethod
    def _is_tool_error(content) -> bool:
        if isinstance(content, dict):
            return any(key in content for key in ("error", "errors", "exception"))

        text = str(content).strip().lower()
        return (
            text.startswith("error:")
            or text.startswith("tool error:")
            or text.startswith("exception:")
            or "traceback (most recent call last)" in text
        )

    def _get_coral_server(self) -> MCPServerStdio:
        """Reuse the Coral MCP server connection to avoid cold starts."""
        if AuraGuardAgent._coral_server is None:
            AuraGuardAgent._coral_server = MCPServerStdio(
                self.coral_bin,
                args=["mcp-stdio"],
                env=os.environ.copy(),
                timeout=GLOBAL_TIMEOUT,
                include_instructions=True,
                max_retries=15, # Allow enough retries for the agent to fix syntax/schema mistakes based on tool errors
            )
        return AuraGuardAgent._coral_server

    def _build_agent(self) -> Agent:
        return Agent(
            self.model,
            instructions=SYSTEM_PROMPT,
            toolsets=[self._get_coral_server()],
            model_settings=ModelSettings(max_tokens=MAX_OUTPUT_TOKENS, temperature=0.0),
        )

    def _unwrap_exception(self, e: Exception) -> str:
        """Helper to get the actual error message from ExceptionGroups or TaskGroups."""
        # Python 3.11+ ExceptionGroup support
        if hasattr(e, "exceptions") and e.exceptions:
            # Recursively unwrap the first sub-exception
            return self._unwrap_exception(e.exceptions[0])
        return str(e)

    async def run_sql(self, sql_query: str) -> list[dict]:
        """Execute a raw SQL query directly against Coral MCP and return rows."""
        # Reuse the pooled server
        server = self._get_coral_server()
        start_time = time.perf_counter()
        
        try:
            # Access the underlying session if available, or use the server context
            async with server:
                # Pydantic AI's MCPServerStdio doesn't expose the session directly in a stable way
                # so we'll use a direct mcp client for raw SQL to ensure reliability and speed
                from mcp.client.stdio import stdio_client
                from mcp import ClientSession, StdioServerParameters

                params = StdioServerParameters(
                    command=self.coral_bin,
                    args=["mcp-stdio"],
                    env=os.environ.copy(),
                )

                async with stdio_client(params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool("sql", {"sql": sql_query})
                        
                        elapsed = time.perf_counter() - start_time
                        logger.info("Coral Query executed in %.3fs: %s", elapsed, sql_query)
                        print(f"[CORAL SQL] {elapsed:.3f}s | {sql_query[:100]}...")

                        if result.isError:
                            error_text = "".join(p.text for p in result.content if hasattr(p, "text"))
                            
                            # Handle 404s silently (expected for many repos that don't have certain manifests)
                            if "(404)" in error_text:
                                logger.info("Resource not found (404) for query [%s]. Skipping silently.", sql_query[:50])
                                return []

                            logger.error("Coral SQL Error for query [%s]: %s", sql_query, error_text)
                            raise RuntimeError(f"Coral SQL Error: {error_text}")
                        
                        for part in result.content:
                            if hasattr(part, "text") and part.text:
                                try:
                                    data = json.loads(part.text)
                                    if isinstance(data, dict) and "rows" in data:
                                        return data["rows"]
                                    if isinstance(data, list):
                                        return data
                                except json.JSONDecodeError:
                                    continue
                        return []
        except Exception as e:
            msg = self._unwrap_exception(e)
            logger.error("Failed to run SQL [%s]: %s\n%s", sql_query, msg, traceback.format_exc())
            raise RuntimeError(msg) from e

    async def fast_repo_scan(self, owner: str, repo: str) -> dict:
        """Fetch package manifest (JS/Py/Rust) AND perform deep PR security audit."""
        findings = []
        # 1. Fetch current main manifests
        manifest_files = [("package.json", "npm"), ("requirements.txt", "PyPI"), ("Cargo.toml", "Cargo")]
        for filename, ecosystem in manifest_files:
            sql = f"SELECT content_text FROM github.contents WHERE owner = '{owner}' AND repo = '{repo}' AND path = '{filename}'"
            try:
                rows = await self.run_sql(sql)
                if rows:
                    findings.extend(await self._check_manifest_vulnerabilities(owner, repo, rows[0]["content_text"], filename, ecosystem))
            except: continue

        # 2. Deep PR Audit (Delta Security Scan)
        pr_alerts = []
        prs_sql = f"SELECT number, title, head__sha, base__sha FROM github.pulls WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'open' LIMIT 5"
        try:
            prs = await self.run_sql(prs_sql)
            for pr in prs:
                # Compare manifest in head vs base
                for filename, ecosystem in manifest_files:
                    try:
                        # Get Head Manifest
                        head_sql = f"SELECT content_text FROM github.contents WHERE owner = '{owner}' AND repo = '{repo}' AND path = '{filename}' AND ref = '{pr['head__sha']}'"
                        base_sql = f"SELECT content_text FROM github.contents WHERE owner = '{owner}' AND repo = '{repo}' AND path = '{filename}' AND ref = '{pr['base__sha']}'"
                        
                        head_rows = await self.run_sql(head_sql)
                        base_rows = await self.run_sql(base_sql)
                        
                        if head_rows and base_rows:
                            head_vulns = await self._check_manifest_vulnerabilities(owner, repo, head_rows[0]["content_text"], filename, ecosystem)
                            base_vulns = await self._check_manifest_vulnerabilities(owner, repo, base_rows[0]["content_text"], filename, ecosystem)
                            
                            # Identify NEWLY introduced vulnerabilities
                            base_cves = {v['cve_id'] for v in base_vulns}
                            new_vulns = [v for v in head_vulns if v['cve_id'] not in base_cves]
                            
                            if new_vulns:
                                pr_alerts.append({
                                    "pr_number": pr["number"],
                                    "pr_title": pr["title"],
                                    "newly_introduced_vulnerabilities": new_vulns
                                })
                    except: continue
        except: pass

        return {
            "repository": f"{owner}/{repo}",
            "current_vulnerabilities": findings,
            "high_risk_pull_requests": pr_alerts
        }

    async def _check_manifest_vulnerabilities(self, owner: str, repo: str, content: str, filename: str, ecosystem: str) -> list[dict]:
        """Helper to parse manifest and query OSV."""
        deps = {}
        if filename == "package.json":
            try:
                manifest = json.loads(content)
                deps = {**manifest.get("dependencies", {}), **manifest.get("devDependencies", {})}
            except: return []
        elif filename == "requirements.txt":
            for line in content.splitlines():
                if "==" in line:
                    parts = line.split("==")
                    deps[parts[0].strip()] = parts[1].strip()
        
        findings = []
        for pkg, ver in list(deps.items())[:10]:
            clean_ver = "".join(c for c in ver if c.isdigit() or c == '.')
            if not clean_ver: continue
            osv_sql = f"SELECT * FROM osv.query_by_version WHERE package_name = '{pkg}' AND version = '{clean_ver}' AND ecosystem = '{ecosystem}'"
            try:
                vulns = await self.run_sql(osv_sql)
                for v in vulns:
                    findings.append({"package_name": pkg, "current_version": ver, "cve_id": v.get("id"), "severity": v.get("severity"), "summary": v.get("summary")})
            except: continue
        return findings

    async def fast_org_scan(self, owner: str) -> list[dict]:
        """Fetch all repositories and perform a comprehensive Repo+PR scan on the first 3."""
        repos_sql = f"SELECT name FROM github.repositories WHERE owner__login = '{owner}' LIMIT 3"
        try:
            repos = await self.run_sql(repos_sql)
            all_data = []
            for r in repos:
                repo_scan_result = await self.fast_repo_scan(owner, r["name"])
                all_data.append(repo_scan_result)
            return all_data
        except Exception as e:
            logger.error("Fast org scan failed for %s: %s", owner, e)
            return []

    async def summarize_data(self, rows: list[dict], prompt_template: str, context: dict) -> str:
        """One-shot LLM call to summarize pre-fetched Coral rows into a report.
        Uses a specialized prompt to ensure it generates a final report immediately.
        """
        today = datetime.now().strftime("%B %d, %Y")
        summary_prompt = (
            "You are an SRE Expert. You will be provided with RAW DATA in JSON format. "
            "Your task is to analyze this data and write a SHORT and SIMPLE FINAL SRE REPORT immediately. "
            f"Use Date: {today} in the report header. "
            "Avoid wordy preambles. Focus on Summary, Findings, and Action Items. "
            "Do NOT mention 'pending execution' or 'waiting for tools'. "
            "Use the provided data to fill all report sections. If data is missing for a section, state 'No data found'.\n\n"
        )
        
        # Create a pure agent without toolsets
        pure_agent = Agent(self.model, instructions=summary_prompt)
        
        rows_json = json.dumps(rows, indent=2)
        try:
            full_prompt = prompt_template.replace("{rows_json}", rows_json)
        except:
            full_prompt = f"{prompt_template}\n\nDATA:\n{rows_json}"
        
        if context:
            full_prompt = f"CONTEXT: {json.dumps(context)}\n\n{full_prompt}"

        try:
            result = await pure_agent.run(full_prompt)
            data = getattr(result, 'data', getattr(result, 'output', str(result)))
            return str(data).strip()
        except Exception as e:
            msg = self._unwrap_exception(e)
            logger.error("Failed to summarize data: %s\n%s", msg, traceback.format_exc())
            return f"Error generating summary: {msg}"
