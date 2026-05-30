"""
Org-Wide Supply-Chain Scanner — commands/org_scan.py

Receives pre-fetched org-wide CVE scan rows (already queried from Coral MCP
by the agent) and generates a prioritised LLM-powered remediation report.

The agent is responsible for:
  1. Cross-joining github.org_repos × github.package_deps × osv.query_by_version
  2. Passing the resulting rows to triage.py org-scan --rows '<json>'
"""

from __future__ import annotations

import logging
import sys
from typing import TypedDict

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class OrgScanRow(TypedDict):
    repo: str
    package_name: str
    current_version: str
    cve_id: str
    severity: str
    summary: str
    fixed_version: str


_VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}

# Columns forwarded to the LLM
_ORG_SCAN_COLUMNS = frozenset({
    "repo", "package_name", "current_version",
    "cve_id", "severity", "summary", "fixed_version",
})


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_and_filter_rows(rows: list[dict]) -> list[OrgScanRow]:
    """Validate org-scan rows. Incomplete rows are logged and excluded."""
    valid: list[OrgScanRow] = []
    for row in rows:
        repo = row.get("repo", "")
        package_name = row.get("package_name", "")
        cve_id = row.get("cve_id", "")
        severity = row.get("severity", "").upper()

        if not repo or not package_name or not cve_id:
            logger.warning("Skipping incomplete org-scan row: %r", row)
            continue

        valid.append(OrgScanRow(
            repo=repo,
            package_name=package_name,
            current_version=row.get("current_version", "unknown"),
            cve_id=cve_id,
            severity=severity if severity in _VALID_SEVERITIES else "UNKNOWN",
            summary=row.get("summary", ""),
            fixed_version=row.get("fixed_version", ""),
        ))

    # Sort: CRITICAL first, then HIGH, MEDIUM, LOW, then by repo name
    _order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
    valid.sort(key=lambda r: (_order.get(r["severity"], 4), r["repo"]))
    return valid


# ---------------------------------------------------------------------------
# LLM prompt
# ---------------------------------------------------------------------------

_ORG_SCAN_PROMPT = """\
You are a senior SRE and security engineer. The following data shows recent CVE
findings from the OSV database affecting packages used across our organisation's
microservices.

For each affected service produce:
1. A clear summary of the vulnerability and its severity
2. Which microservice(s) are exposed and the affected package version
3. A concrete remediation action (upgrade path, patch, or accept-risk justification)
4. An overall org-level risk score and prioritised action list

Findings sorted by severity (compact JSON):
{rows_json}"""


# ---------------------------------------------------------------------------
# Entry point (called by triage.py after agent fetches rows)
# ---------------------------------------------------------------------------

def analyse_and_report(
    scan_rows: list[dict],
    owner: str,
) -> None:
    """Validate rows and generate the org-wide CVE scan SRE report.

    Args:
        scan_rows: Raw rows from Coral org-wide cross-join query.
        owner: GitHub org/user.

    Exit codes:
        0 — org is clean, no CVEs found
        1 — vulnerabilities found (report printed)
        2 — LLM unavailable (fallback table printed)
    """
    from commands.llm_gateway import call_llm, LLMError

    if not scan_rows:
        print(f"✅ No CVEs found across '{owner}' repos — org is clean.")
        sys.exit(0)

    valid_rows = validate_and_filter_rows(scan_rows)

    if not valid_rows:
        print("✅ No valid CVE rows after validation.")
        sys.exit(0)

    # Filter to LLM-safe columns only
    filtered = [
        {k: v for k, v in row.items() if k in _ORG_SCAN_COLUMNS}
        for row in valid_rows
    ]

    context = {"command": "org-scan", "owner": owner}

    try:
        report = call_llm(filtered, _ORG_SCAN_PROMPT, context)
        print("🛡️ AURA GUARD ORG-WIDE SUPPLY-CHAIN SCAN REPORT")
        print(f"Organisation: {owner}  |  {len(valid_rows)} finding(s)")
        print("=" * 60)
        print(report)
    except LLMError as exc:
        print("🛡️ AURA GUARD ORG-WIDE SUPPLY-CHAIN SCAN REPORT (LLM unavailable)")
        print(f"Organisation: {owner}  |  {len(valid_rows)} finding(s)")
        print("=" * 60)
        print(f"{'REPO':<28} {'PACKAGE':<22} {'VER':<10} {'CVE':<20} SEV")
        print("-" * 95)
        for row in valid_rows:
            print(
                f"{row.get('repo',''):<28} "
                f"{row.get('package_name',''):<22} "
                f"{row.get('current_version',''):<10} "
                f"{row.get('cve_id',''):<20} "
                f"{row.get('severity','')}"
            )
        print(f"\nLLM error: {exc.message}", file=sys.stderr)
        sys.exit(2)

    sys.exit(1)
