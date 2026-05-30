from __future__ import annotations

import json
import os
import logging
from typing import List, Optional

from pydantic_ai import Agent, ModelSettings
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.usage import UsageLimits
from pydantic_ai.exceptions import UnexpectedModelBehavior, UsageLimitExceeded

# Default to Gemini
DEFAULT_MODEL = "google:gemini-1.5-flash"
MAX_OUTPUT_TOKENS = 8192

SYSTEM_PROMPT = """You are a Pydantic AI SRE assistant for Aura Guard, operating via Native Coral MCP.

Operating principles:
- You use the tools provided by the Coral MCP server (like `mcp_coral_sql`) to fetch evidence.
- NEVER fabricate data. If you cannot find data, say "No evidence found."
- **No Cartesian Products**: Never join large tables (like commits to logs) without temporal constraints or exact IDs. 

You handle three specific types of investigations. Format your response using Markdown headers (##) based on the task:

1. **Incident Triage (Chain of Thought)**
   - Step 1: Query `cloudwatch_logs.log_events` for errors related to the service. Get exact timestamps.
   - Step 2: Query `github.commits` within a **3-day window** preceding the earliest error.
   - Step 3: Query `linear.issues` to correlate the commit message to intent.
   - **Report Format**:
     ## Summary
     ## Evidence (Use tables)
     ## Likely cause (Include Confidence: High/Medium/Low)
     ## Blast radius
     ## What changed
     ## Mitigation
     ## Sources ([Source Name] [ID](URL))

2. **Supply Chain Audit**
   - Query `github.contents` to read `package.json`, `Cargo.toml`, or `requirements.txt`.
   - Extract dependencies and join them with `osv.query_by_version` to find vulnerabilities.
   - If a PR is specified, compare `github.pulls` base and head SHAs to find *new* vulnerabilities.
   - **Report Format**:
     ## Audit Summary
     ## Vulnerabilities Found (Markdown table: Package, Version, CVE, Severity)
     ## Risk Assessment
     ## Remediation Steps
     ## Sources

3. **Blast Radius Evaluation**
   - Query `github.search_code` to find repositories importing a specific file/package.
   - Query `github.pulls` to see if those downstream repos have active PRs that will be affected.
   - **Report Format**:
     ## Impact Summary
     ## Affected Downstream Repositories
     ## Active Pull Requests at Risk
     ## Notification Plan
     ## Sources
"""

class AuraGuardAgent:
    def __init__(
        self,
        model: str | None = None,
        max_tool_rounds: int = 25,
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

    def _build_agent(self, event_stream_handler=None) -> Agent:
        # Register Coral as an MCP server
        coral_server = MCPServerStdio(
            self.coral_bin,
            args=["mcp-stdio"],
            env=os.environ.copy(),
            timeout=30,
            include_instructions=True,
        )
        
        return Agent(
            self.model,
            instructions=SYSTEM_PROMPT,
            toolsets=[coral_server],
            model_settings=ModelSettings(max_tokens=MAX_OUTPUT_TOKENS, temperature=0.0),
            event_stream_handler=event_stream_handler,
        )

    async def investigate(
        self,
        query: str,
        on_event=None,
    ) -> str:
        agent = self._build_agent(event_stream_handler=None)
        try:
            async with agent:
                result = await agent.run(
                    query,
                    usage_limits=UsageLimits(request_limit=self.max_tool_rounds),
                )
                return str(result.output).strip()
        except UsageLimitExceeded:
            return "Investigation reached tool-call limit. Analysis is incomplete."
        except UnexpectedModelBehavior as exc:
            return f"Agent encountered an error during investigation: {str(exc)}"
        except Exception as e:
            return f"Internal Agent Error: {str(e)}"

        except UsageLimitExceeded:
            return "Investigation reached tool-call limit. Analysis is incomplete."
        except UnexpectedModelBehavior as exc:
            return f"Agent encountered an error during investigation: {str(exc)}"
        except Exception as e:
            return f"Internal Agent Error: {str(e)}"
