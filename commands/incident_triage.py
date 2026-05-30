"""
Incident Investigator — commands/incident_triage.py

Receives federated rows (Logs + Commits + Tickets) and generates
an LLM-powered RCA (Root Cause Analysis) report.
"""

from __future__ import annotations

import logging
import sys
from typing import TypedDict

logger = logging.getLogger(__name__)

class IncidentRow(TypedDict):
    timestamp: int | str
    log_message: str
    developer: str
    commit_message: str
    ticket_id: str
    ticket_title: str
    ticket_context: str

def validate_rows(rows: list[dict]) -> list[dict]:
    """Validate and clean incident rows."""
    valid: list[dict] = []
    for row in rows:
        # We allow some fields to be missing (e.g. no ticket found)
        # but we must at least have log data and commit data.
        log_msg = row.get("log_message") or row.get("message")
        commit_msg = row.get("commit_message") or row.get("message")
        
        if not log_msg:
            logger.warning("Skipping row without log message: %r", row)
            continue
            
        valid.append({
            "timestamp": row.get("timestamp", "unknown"),
            "log_message": log_msg,
            "developer": row.get("developer") or row.get("author", "unknown"),
            "commit_message": commit_msg or "unknown",
            "ticket_id": row.get("ticket_id") or row.get("identifier", "N/A"),
            "ticket_title": row.get("ticket_title") or row.get("title", "N/A"),
            "ticket_context": row.get("ticket_context") or row.get("description", "N/A")
        })
    return valid

_INCIDENT_PROMPT = """You are a senior SRE. Analyze the following federated incident data
which joins CloudWatch error logs, recent GitHub commits, and Linear tickets.

Your goal is to perform Root-Cause Analysis (RCA).
Include:
- **Summary of the Production Error**: What specifically is failing?
- **The Suspected Culprit**: Which commit or developer likely introduced the bug?
- **Ticket Context**: Why was this change made in the first place?
- **Suggested Fix**: Provide a concrete, technical recommendation to resolve the issue.

Incident Data (compact JSON):
{rows_json}"""

def analyse_and_report(
    incident_rows: list[dict],
    owner: str,
    service: str,
) -> None:
    """Entry point for CLI or local calls."""
    from commands.llm_gateway import call_llm, LLMError

    if not incident_rows:
        print(f"✅ No incident patterns found for service '{service}'.")
        sys.exit(0)

    valid_rows = validate_rows(incident_rows)
    
    context = {"command": "incident-triage", "owner": owner, "service": service}

    try:
        report = call_llm(valid_rows, _INCIDENT_PROMPT, context)
        print("🛡️ AURA GUARD INCIDENT INVESTIGATION REPORT")
        print(f"Service: {service}  |  Owner: {owner}")
        print("=" * 60)
        print(report)
    except LLMError as exc:
        print("🛡️ AURA GUARD INCIDENT REPORT (Fallback Data)")
        print(json.dumps(valid_rows, indent=2))
        print(f"\nLLM error: {exc.message}", file=sys.stderr)
        sys.exit(2)
