"""
Data models for Aura Guard.

Defines typed data structures for vulnerability rows, blast-radius rows,
and Coral query results, along with validation functions that enforce
field-level constraints before data is forwarded to the LLM or printed
in reports.
"""

from __future__ import annotations

import re
from typing import TypedDict

# ---------------------------------------------------------------------------
# TypedDict definitions
# ---------------------------------------------------------------------------

VALID_RISK_LEVELS = frozenset({"CRITICAL", "HIGH", "MEDIUM", "LOW"})
CVE_ID_PATTERN = re.compile(r"^CVE-\d{4}-\d+$")


class VulnerabilityRow(TypedDict):
    """A single CVE finding returned by the OSV cross-join query.

    Fields
    ------
    filename:
        The file in the PR that introduced the vulnerable dependency
        (e.g. ``"package.json"``).
    cve_id:
        The CVE identifier in the format ``CVE-<year>-<id>``
        (e.g. ``"CVE-2026-12345"``).
    vulnerability_details:
        Human-readable OSV advisory summary describing the vulnerability.
    risk_level:
        Severity tier — one of ``"CRITICAL"``, ``"HIGH"``, ``"MEDIUM"``,
        or ``"LOW"``.
    """

    filename: str
    cve_id: str
    vulnerability_details: str
    risk_level: str


class BlastRadiusRow(TypedDict):
    """A single downstream impact record from the org-wide cross-join query.

    Fields
    ------
    downstream_repo:
        Name of the downstream repository that imports the target file/library.
    active_pr:
        Open pull-request number in the downstream repository (must be >= 1).
    developer:
        GitHub login of the PR author in the downstream repository.
    manifest_data:
        Raw snippet of the downstream ``package.json`` content that references
        the target library.
    """

    downstream_repo: str
    active_pr: int
    developer: str
    manifest_data: str


class CoralQueryResult(TypedDict):
    """The result envelope returned by a Coral SQL query execution.

    Fields
    ------
    rows:
        Deserialized list of row dicts returned by the Coral runtime.
    row_count:
        Number of rows in ``rows`` (convenience field; equals ``len(rows)``).
    elapsed_ms:
        Wall-clock time in milliseconds from HTTP send to full response
        deserialization.  Must be non-negative.  Values >= 500 trigger a
        slow-query warning.
    """

    rows: list[dict]
    row_count: int
    elapsed_ms: float


# ---------------------------------------------------------------------------
# Validation functions
# ---------------------------------------------------------------------------


def validate_vulnerability_row(row: dict) -> VulnerabilityRow:
    """Validate and return a :class:`VulnerabilityRow` from a raw dict.

    Enforces:

    * ``risk_level`` must be one of ``"CRITICAL"``, ``"HIGH"``, ``"MEDIUM"``,
      or ``"LOW"``.
    * ``cve_id`` must match the pattern ``CVE-\\d{4}-\\d+``.
    * ``filename`` must be a non-empty string.

    Parameters
    ----------
    row:
        Raw dict (e.g. from a Coral query result) to validate.

    Returns
    -------
    VulnerabilityRow
        The same dict cast to :class:`VulnerabilityRow` after all checks pass.

    Raises
    ------
    ValueError
        If any validation rule is violated.  The message identifies the
        failing field and the offending value.
    """
    # --- filename ---
    filename = row.get("filename", "")
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError(
            f"VulnerabilityRow.filename must be a non-empty string; "
            f"got {filename!r}"
        )

    # --- cve_id ---
    cve_id = row.get("cve_id", "")
    if not isinstance(cve_id, str) or not CVE_ID_PATTERN.match(cve_id):
        raise ValueError(
            f"VulnerabilityRow.cve_id must match CVE-\\d{{4}}-\\d+; "
            f"got {cve_id!r}"
        )

    # --- risk_level ---
    risk_level = row.get("risk_level", "")
    if risk_level not in VALID_RISK_LEVELS:
        raise ValueError(
            f"VulnerabilityRow.risk_level must be one of "
            f"{sorted(VALID_RISK_LEVELS)}; got {risk_level!r}"
        )

    return VulnerabilityRow(
        filename=row["filename"],
        cve_id=row["cve_id"],
        vulnerability_details=row.get("vulnerability_details", ""),
        risk_level=row["risk_level"],
    )


def validate_blast_radius_row(row: dict) -> BlastRadiusRow:
    """Validate and return a :class:`BlastRadiusRow` from a raw dict.

    Enforces:

    * ``active_pr`` must be an integer >= 1.
    * ``downstream_repo`` must be a non-empty string.
    * ``developer`` must be a non-empty string.

    Parameters
    ----------
    row:
        Raw dict (e.g. from a Coral query result) to validate.

    Returns
    -------
    BlastRadiusRow
        The same dict cast to :class:`BlastRadiusRow` after all checks pass.

    Raises
    ------
    ValueError
        If any validation rule is violated.  The message identifies the
        failing field and the offending value.
    """
    # --- downstream_repo ---
    downstream_repo = row.get("downstream_repo", "")
    if not isinstance(downstream_repo, str) or not downstream_repo.strip():
        raise ValueError(
            f"BlastRadiusRow.downstream_repo must be a non-empty string; "
            f"got {downstream_repo!r}"
        )

    # --- developer ---
    developer = row.get("developer", "")
    if not isinstance(developer, str) or not developer.strip():
        raise ValueError(
            f"BlastRadiusRow.developer must be a non-empty string; "
            f"got {developer!r}"
        )

    # --- active_pr ---
    active_pr = row.get("active_pr")
    if not isinstance(active_pr, int) or isinstance(active_pr, bool) or active_pr < 1:
        raise ValueError(
            f"BlastRadiusRow.active_pr must be an integer >= 1; "
            f"got {active_pr!r}"
        )

    return BlastRadiusRow(
        downstream_repo=row["downstream_repo"],
        active_pr=row["active_pr"],
        developer=row["developer"],
        manifest_data=row.get("manifest_data", ""),
    )
