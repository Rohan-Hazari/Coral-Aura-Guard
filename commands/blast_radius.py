"""
Blast-Radius Evaluator — commands/blast_radius.py

Receives pre-fetched downstream impact rows (already queried from Coral MCP
by the agent) and generates an LLM-powered SRE blast-radius report.

The agent is responsible for:
  1. Cross-joining github.org_repos × github.pulls × github.contents via Coral
  2. Passing the resulting rows to triage.py blast-radius --rows '<json>'
"""

from __future__ import annotations

import logging
import sys

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_and_filter_rows(rows: list[dict]) -> list[dict]:
    """Validate blast-radius rows. Invalid rows are logged and excluded."""
    from models import validate_blast_radius_row

    valid: list[dict] = []
    for row in rows:
        try:
            valid.append(validate_blast_radius_row(row))
        except ValueError as exc:
            logger.warning("Invalid blast-radius row excluded: %s — %r", exc, row)
    return valid


# ---------------------------------------------------------------------------
# LLM prompt
# ---------------------------------------------------------------------------

_BLAST_RADIUS_PROMPT = """\
You are a senior SRE. Analyze the following downstream impact data and produce
a concise, terminal-optimized SRE markdown blast-radius report.

Include:
- How many downstream repositories are affected
- The open PRs and developers at risk
- Concrete action items (notify owners, block merge, coordinate rollout)
- An overall risk assessment

Downstream impact data (compact JSON):
{rows_json}"""


# ---------------------------------------------------------------------------
# Entry point (called by triage.py after agent fetches rows)
# ---------------------------------------------------------------------------

def analyse_and_report(
    impact_rows: list[dict],
    file_path: str,
    owner: str,
) -> None:
    """Validate rows and generate the blast-radius SRE report.

    Args:
        impact_rows: Raw rows from Coral cross-join query.
        file_path: The library/file being evaluated.
        owner: GitHub org/user.

    Exit codes:
        0 — no downstream impact
        1 — blast radius detected (report printed)
        2 — LLM unavailable (fallback table printed)
    """
    from commands.llm_gateway import call_llm, LLMError

    if not impact_rows:
        print(f"✅ No downstream impact detected for '{file_path}'.")
        sys.exit(0)

    valid_rows = validate_and_filter_rows(impact_rows)

    if not valid_rows:
        print("✅ No valid downstream impact rows after validation.")
        sys.exit(0)

    context = {"command": "blast-radius", "file_path": file_path, "owner": owner}

    try:
        report = call_llm(valid_rows, _BLAST_RADIUS_PROMPT, context)
        print("🛡️ AURA GUARD BLAST-RADIUS REPORT")
        print(f"Library: {file_path} · Org: {owner}")
        print("=" * 60)
        print(report)
    except LLMError as exc:
        print("🛡️ AURA GUARD BLAST-RADIUS REPORT (LLM unavailable — raw data)")
        print(f"Library: {file_path} · Org: {owner}")
        print("=" * 60)
        print(f"{'DOWNSTREAM REPO':<35} {'ACTIVE PR':<12} DEVELOPER")
        print("-" * 70)
        for row in valid_rows:
            print(
                f"{row.get('downstream_repo','N/A'):<35} "
                f"{str(row.get('active_pr','N/A')):<12} "
                f"{row.get('developer','N/A')}"
            )
        print(f"\nLLM error: {exc.message}", file=sys.stderr)
        sys.exit(2)

    sys.exit(1)
