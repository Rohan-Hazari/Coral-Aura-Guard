"""
Supply Chain Auditor — commands/supply_chain.py

Receives pre-fetched CVE rows (already queried from Coral MCP by the agent),
validates them, and generates an LLM-powered SRE security report.
"""

from __future__ import annotations

import json
import logging
import re
import sys

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Version normalisation
# ---------------------------------------------------------------------------

_RANGE_OPERATORS = [">=", "<=", "^", "~", ">"]
_NON_REGISTRY_PREFIXES = (
    "git+", "github:", "gitlab:", "bitbucket:",
    "file:", "http://", "https://", "/", "./", "../",
)
_NON_NUMERIC_ALIASES = {
    "latest", "next", "stable", "beta", "alpha", "canary",
    "rc", "dev", "experimental", "lts", "current", "nightly",
}
_NORMALIZED_RE = re.compile(r"^\d+(\.\d+)*$")


def normalize_version(version: str) -> str | None:
    """Normalize a semver/npm version string to digits-and-dots only."""
    if not isinstance(version, str):
        return None
    v = version.strip()
    if not v:
        return None
    if v.startswith(_NON_REGISTRY_PREFIXES):
        return None
    if "||" in v or " - " in v:
        return None
    if v.lower() in _NON_NUMERIC_ALIASES:
        return None
    for op in _RANGE_OPERATORS:
        if v.startswith(op):
            v = v[len(op):].strip()
            break
    if v in ("*", "x", "X"):
        return None
    if "*" in v or re.search(r"(?<!\d)[xX](?!\d)", v):
        return None
    if " " in v:
        return None
    if not _NORMALIZED_RE.match(v):
        return None
    return v


def parse_package_json_content(content: str) -> list[tuple[str, str, str]]:
    """Parse package.json and return (name, version, ecosystem) tuples."""
    try:
        pkg = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse package.json: %s", exc)
        return []

    result: list[tuple[str, str, str]] = []
    for section in ("dependencies", "devDependencies"):
        section_data = pkg.get(section)
        if not isinstance(section_data, dict):
            continue
        for name, raw_version in section_data.items():
            normalized = normalize_version(raw_version)
            if name and normalized:
                result.append((name, normalized, "npm"))
    return result


def parse_cargo_toml_content(content: str) -> list[tuple[str, str, str]]:
    """Parse Cargo.toml and return (name, version, ecosystem) tuples."""
    result: list[tuple[str, str, str]] = []
    in_deps = False
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and "dependencies" in line:
            in_deps = True
            continue
        if line.startswith("[") and in_deps:
            in_deps = False
            continue
        if in_deps:
            match = re.search(r'^([\w-]+)\s*=\s*(?:"([^"]+)"|\{\s*version\s*=\s*"([^"]+)"[^}]*\})', line)
            if match:
                name = match.group(1)
                ver = match.group(2) or match.group(3)
                normalized = normalize_version(ver)
                if name and normalized:
                    result.append((name, normalized, "crates.io"))
    return result


def parse_requirements_txt_content(content: str) -> list[tuple[str, str, str]]:
    """Parse requirements.txt and return (name, version, ecosystem) tuples."""
    result: list[tuple[str, str, str]] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "-r", "-e")):
            continue
        match = re.search(r'^([\w.-]+)==([\w.-]+)', line)
        if match:
            name = match.group(1)
            ver = match.group(2)
            normalized = normalize_version(ver)
            if name and normalized:
                result.append((name, normalized, "PyPI"))
    return result


def calculate_delta_dependencies(base_deps: list[tuple[str, str, str]], head_deps: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    """Compare two dependency lists and return only what was added or updated in head."""
    base_map = {name: (ver, eco) for name, ver, eco in base_deps}
    delta = []
    for name, ver, eco in head_deps:
        if name not in base_map or base_map[name] != (ver, eco):
            delta.append((name, ver, eco))
    return delta


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_and_filter_rows(rows: list[dict]) -> tuple[list[dict], bool]:
    """Validate CVE rows. Returns (valid_rows, had_invalid)."""
    from models import validate_vulnerability_row
    valid: list[dict] = []
    had_invalid = False
    for row in rows:
        try:
            valid.append(validate_vulnerability_row(row))
        except ValueError as exc:
            logger.error("Invalid vulnerability row excluded: %s — %r", exc, row)
            had_invalid = True
    return valid, had_invalid

# ---------------------------------------------------------------------------
# LLM Gateway Interface
# ---------------------------------------------------------------------------

def analyse_and_report(
    vuln_rows: list[dict],
    context_data: dict,
) -> None:
    from commands.llm_gateway import call_llm, LLMError
    valid_rows, had_invalid = validate_and_filter_rows(vuln_rows)
    
    prompt = """Analyze the following CVE findings and produce an SRE report.
Vulnerability findings (compact JSON):
{rows_json}"""

    try:
        report = call_llm(valid_rows, prompt, context_data)
        print(report)
    except LLMError as exc:
        print(f"LLM Error: {exc.message}")
