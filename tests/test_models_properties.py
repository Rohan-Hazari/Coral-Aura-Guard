"""
Property-based tests for data model validation functions in models.py.

Uses hypothesis to verify universal correctness properties across all valid
and invalid inputs for VulnerabilityRow and BlastRadiusRow validation.
"""

import re

import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st

from models import (
    VALID_RISK_LEVELS,
    CVE_ID_PATTERN,
    validate_vulnerability_row,
    validate_blast_radius_row,
)

# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

# Strategy for valid CVE year (4-digit year)
cve_year = st.integers(min_value=1000, max_value=9999).map(str)

# Strategy for valid CVE numeric id (one or more digits)
cve_numeric_id = st.integers(min_value=0, max_value=999999999).map(str)

# Strategy for valid cve_id strings matching CVE-\d{4}-\d+
valid_cve_id = st.builds(
    lambda year, num: f"CVE-{year}-{num}",
    year=cve_year,
    num=cve_numeric_id,
)

# Strategy for valid risk_level values
valid_risk_level = st.sampled_from(sorted(VALID_RISK_LEVELS))

# Strategy for non-empty strings (filenames, repo names, developer logins)
non_empty_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    min_size=1,
    max_size=200,
).filter(lambda s: s.strip())

# Strategy for positive integers (active_pr >= 1)
positive_int = st.integers(min_value=1, max_value=10_000_000)


# ---------------------------------------------------------------------------
# Property 2: CVE severity is always a valid tier
# Validates: Requirements 4.3, 8.1
# ---------------------------------------------------------------------------

class TestProperty2CVESeverityValidTier:
    """
    **Property 2: CVE severity is always a valid tier**

    For any VulnerabilityRow returned by validate_vulnerability_row,
    risk_level is in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}.

    Validates: Requirements 4.3, 8.1
    """

    @given(
        filename=non_empty_text,
        cve_id=valid_cve_id,
        risk_level=valid_risk_level,
        vulnerability_details=st.text(max_size=500),
    )
    def test_valid_row_risk_level_is_valid_tier(
        self, filename, cve_id, risk_level, vulnerability_details
    ):
        """For any valid input, the returned row's risk_level is a valid tier."""
        row = {
            "filename": filename,
            "cve_id": cve_id,
            "risk_level": risk_level,
            "vulnerability_details": vulnerability_details,
        }
        result = validate_vulnerability_row(row)
        assert result["risk_level"] in VALID_RISK_LEVELS

    @given(
        filename=non_empty_text,
        cve_id=valid_cve_id,
        vulnerability_details=st.text(max_size=500),
        invalid_risk_level=st.text(min_size=1).filter(
            lambda s: s not in VALID_RISK_LEVELS
        ),
    )
    def test_invalid_risk_level_raises_value_error(
        self, filename, cve_id, vulnerability_details, invalid_risk_level
    ):
        """For any invalid risk_level, validate_vulnerability_row raises ValueError."""
        row = {
            "filename": filename,
            "cve_id": cve_id,
            "risk_level": invalid_risk_level,
            "vulnerability_details": vulnerability_details,
        }
        with pytest.raises(ValueError):
            validate_vulnerability_row(row)


# ---------------------------------------------------------------------------
# Property 7: CVE id format is always valid
# Validates: Requirements 4.4, 8.2
# ---------------------------------------------------------------------------

class TestProperty7CVEIdFormatValid:
    """
    **Property 7: CVE id format is always valid**

    For any VulnerabilityRow returned by validate_vulnerability_row,
    cve_id matches CVE-\\d{4}-\\d+.

    Validates: Requirements 4.4, 8.2
    """

    @given(
        filename=non_empty_text,
        cve_id=valid_cve_id,
        risk_level=valid_risk_level,
        vulnerability_details=st.text(max_size=500),
    )
    def test_valid_row_cve_id_matches_pattern(
        self, filename, cve_id, risk_level, vulnerability_details
    ):
        """For any valid input, the returned row's cve_id matches CVE-\\d{4}-\\d+."""
        row = {
            "filename": filename,
            "cve_id": cve_id,
            "risk_level": risk_level,
            "vulnerability_details": vulnerability_details,
        }
        result = validate_vulnerability_row(row)
        assert CVE_ID_PATTERN.match(result["cve_id"]) is not None

    @given(
        filename=non_empty_text,
        risk_level=valid_risk_level,
        vulnerability_details=st.text(max_size=500),
        invalid_cve_id=st.text(min_size=1).filter(
            lambda s: not re.match(r"^CVE-\d{4}-\d+$", s)
        ),
    )
    def test_invalid_cve_id_raises_value_error(
        self, filename, risk_level, vulnerability_details, invalid_cve_id
    ):
        """For any cve_id not matching CVE-\\d{4}-\\d+, validate_vulnerability_row raises ValueError."""
        row = {
            "filename": filename,
            "cve_id": invalid_cve_id,
            "risk_level": risk_level,
            "vulnerability_details": vulnerability_details,
        }
        with pytest.raises(ValueError):
            validate_vulnerability_row(row)


# ---------------------------------------------------------------------------
# Property 3: Blast-radius rows reference only open PRs
# Validates: Requirements 5.3, 8.4
# ---------------------------------------------------------------------------

class TestProperty3BlastRadiusOpenPRsOnly:
    """
    **Property 3: Blast-radius rows reference only open PRs**

    For any BlastRadiusRow returned by validate_blast_radius_row,
    active_pr > 0.

    Validates: Requirements 5.3, 8.4
    """

    @given(
        downstream_repo=non_empty_text,
        active_pr=positive_int,
        developer=non_empty_text,
        manifest_data=st.text(max_size=500),
    )
    def test_valid_row_active_pr_is_positive(
        self, downstream_repo, active_pr, developer, manifest_data
    ):
        """For any valid input, the returned row's active_pr is > 0."""
        row = {
            "downstream_repo": downstream_repo,
            "active_pr": active_pr,
            "developer": developer,
            "manifest_data": manifest_data,
        }
        result = validate_blast_radius_row(row)
        assert result["active_pr"] > 0

    @given(
        downstream_repo=non_empty_text,
        developer=non_empty_text,
        manifest_data=st.text(max_size=500),
        invalid_active_pr=st.one_of(
            st.integers(max_value=0),          # zero or negative integers
            st.none(),                          # None
            st.text(min_size=1),               # strings
            st.floats(allow_nan=False),        # floats
            st.booleans(),                     # booleans (bool is subclass of int, but should be rejected)
        ),
    )
    def test_invalid_active_pr_raises_value_error(
        self, downstream_repo, developer, manifest_data, invalid_active_pr
    ):
        """For any active_pr that is not a positive integer, validate_blast_radius_row raises ValueError."""
        # Booleans are a subclass of int in Python; the validator explicitly rejects them
        row = {
            "downstream_repo": downstream_repo,
            "active_pr": invalid_active_pr,
            "developer": developer,
            "manifest_data": manifest_data,
        }
        with pytest.raises(ValueError):
            validate_blast_radius_row(row)
