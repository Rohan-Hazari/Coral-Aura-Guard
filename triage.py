"""
triage.py — Aura Guard Analysis & Reporting CLI

Called by the Coral agent AFTER it has fetched data from Coral MCP.
Receives pre-fetched rows as JSON, validates them, and generates an
LLM-powered SRE report.

The agent extracts owner/repo/PR from what the user says — no env defaults.
Works with any public GitHub org, repo, or PR number.

Usage (called by agent after Coral queries):
    python triage.py supply-chain --rows '<json>' --pr 1042 --owner facebook --repo react
    python triage.py blast-radius --rows '<json>' --file lodash --owner my-org
    python triage.py org-scan     --rows '<json>' --owner my-org

Usage (human, reads rows from a JSON file):
    python triage.py supply-chain --rows-file rows.json --pr 1042 --owner facebook --repo react
    python triage.py org-scan     --rows-file scan.json --owner my-org

Environment variables (from .env):
    MODEL_PROVIDER   — openai | google  (required)
    MODEL_API_KEY    — API key          (required)
    MODEL_NAME       — model name       (optional, has defaults)
    GITHUB_TOKEN     — for private repos (optional)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

class _JsonLinesFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        })


def _configure_logging() -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_JsonLinesFormatter())
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.DEBUG)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_rows(args) -> list[dict]:
    \"\"\"Load rows from --rows (inline JSON) or --rows-file (path).\"\"\"
    raw_json = \"\"
    if hasattr(args, \"rows\") and args.rows:
        raw_json = args.rows
    elif hasattr(args, \"rows_file\") and args.rows_file:
        try:
            with open(args.rows_file, \"r\", encoding=\"utf-8\") as f:
                raw_json = f.read()
        except OSError as e:
            print(f\"Error reading rows file: {e}\", file=sys.stderr)
            sys.exit(1)
    else:
        print(\"Error: provide --rows '<json>' or --rows-file <path>\", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw_json)

        # Check if the input is actually a Coral error object instead of a list of rows
        if isinstance(data, dict) and data.get(\"isError\") or (isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and \"functionResponse\" in data[0]):
            _handle_coral_error(data)
            sys.exit(1)

        if not isinstance(data, list):
            print(\"Error: Coral results must be a JSON array\", file=sys.stderr)
            sys.exit(1)
        return data
    except json.JSONDecodeError as e:
        print(f\"Error: Input is not valid JSON: {e}\", file=sys.stderr)
        sys.exit(1)


def _handle_coral_error(error_data: dict | list) -> None:
    \"\"\"Extract and print user-friendly messages from Coral error payloads.\"\"\"
    msg = \"Unknown Coral error\"
    detail = \"\"

    # Handle structured tool error format
    if isinstance(error_data, list) and len(error_data) > 0:
        res = error_data[0].get(\"functionResponse\", {}).get(\"response\", {})
        if res.get(\"isError\"):
            err = res.get(\"structuredContent\", {}).get(\"error\", {})
            msg = err.get(\"summary\", \"Coral query failed\")
            detail = err.get(\"detail\", \"\")
    elif isinstance(error_data, dict):
        msg = error_data.get(\"summary\", \"Coral query failed\")
        detail = error_data.get(\"detail\", \"\")

    print(f\"❌ CORAL ERROR: {msg}\", file=sys.stderr)
    if detail:
        print(f\"Detail: {detail}\", file=sys.stderr)

    if \"rate limit exceeded\" in detail.lower() or \"429\" in detail:
        print(\"\\n💡 HINT: You are being rate limited by the upstream API (e.g. GitHub).\", file=sys.stderr)
        print(\"Please wait for the duration specified in the error detail before retrying.\", file=sys.stderr)



def _validate_env() -> None:
    # MODEL_API_KEY is only required for standalone use (without an agent like Gemini CLI).
    # When Gemini CLI / Kiro / Claude is driving, they handle LLM calls themselves.
    # We warn but don't exit — triage.py will fail gracefully at call_llm() time if needed.
    if not os.environ.get("MODEL_API_KEY") and not os.environ.get("MODEL_PROVIDER"):
        logging.getLogger(__name__).warning(
            "MODEL_API_KEY and MODEL_PROVIDER not set — "
            "LLM report generation will fail if running standalone. "
            "This is fine when using Gemini CLI or another agent."
        )


def _check_gitignore() -> None:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".gitignore")
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.read().splitlines()]
        if ".env" not in lines:
            logging.getLogger(__name__).warning(
                ".gitignore does not contain .env — credentials may be committed"
            )
    except FileNotFoundError:
        pass


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _add_rows_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--rows", metavar="JSON",
                       help="Coral result rows as an inline JSON array string")
    group.add_argument("--rows-file", metavar="PATH",
                       help="Path to a JSON file containing Coral result rows")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="triage.py",
        description=(
            "Aura Guard — Security analysis & reporting.\n"
            "Works with any public GitHub org, repo, or PR.\n"
            "Called by the Coral agent after fetching data via Coral MCP."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    # supply-chain
    sc = subparsers.add_parser(
        "supply-chain",
        help="Analyse CVE rows from a PR dependency audit and generate SRE report",
    )
    _add_rows_args(sc)
    sc.add_argument("--pr", type=int, required=True,
                    help="Pull-request number (e.g. 1042)")
    sc.add_argument("--owner", required=True,
                    help="GitHub org or user (e.g. facebook, my-org)")
    sc.add_argument("--repo", required=True,
                    help="Repository name (e.g. react, payment-service)")

    # blast-radius
    br = subparsers.add_parser(
        "blast-radius",
        help="Analyse downstream impact rows and generate blast-radius SRE report",
    )
    _add_rows_args(br)
    br.add_argument("--file", required=True,
                    help="Library or file path being evaluated (e.g. lodash, core-billing-utils)")
    br.add_argument("--owner", required=True,
                    help="GitHub org or user to scan")

    # org-scan
    os_cmd = subparsers.add_parser(
        "org-scan",
        help="Analyse org-wide CVE scan rows and generate prioritised remediation report",
    )
    _add_rows_args(os_cmd)
    os_cmd.add_argument("--owner", required=True,
                        help="GitHub org or user that was scanned")

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    _configure_logging()

    try:
        from dotenv import load_dotenv
        load_dotenv(override=False)
    except ImportError:
        pass

    _check_gitignore()
    _validate_env()

    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_usage(sys.stderr)
        print(
            "error: a subcommand is required: supply-chain, blast-radius, org-scan",
            file=sys.stderr,
        )
        sys.exit(1)

    rows = _load_rows(args)

    if args.command == "supply-chain":
        from commands.supply_chain import analyse_and_report
        analyse_and_report(
            vuln_rows=rows,
            pr_number=args.pr,
            owner=args.owner,
            repo=args.repo,
        )

    elif args.command == "blast-radius":
        from commands.blast_radius import analyse_and_report
        analyse_and_report(
            impact_rows=rows,
            file_path=args.file,
            owner=args.owner,
        )

    elif args.command == "org-scan":
        from commands.org_scan import analyse_and_report
        analyse_and_report(
            scan_rows=rows,
            owner=args.owner,
        )


if __name__ == "__main__":
    main()
