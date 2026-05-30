"""
Property-based tests for parse_package_json in commands/supply_chain.py.

Uses hypothesis to verify universal correctness properties across all valid
and invalid inputs for the dependency parsing function.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from hypothesis import given, settings
from hypothesis import strategies as st

from commands.supply_chain import parse_package_json

# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

# Strategy for a file dict that is NOT package.json
non_package_json_file = st.fixed_dictionaries(
    {"filename": st.text(min_size=1, max_size=100).filter(lambda s: s != "package.json")}
)

# Strategy for a list of files that does NOT contain package.json
files_without_package_json = st.lists(
    non_package_json_file,
    min_size=0,
    max_size=10,
)

# Strategy for a valid npm package name (simplified: non-empty, no whitespace)
package_name = st.text(
    alphabet=st.characters(
        whitelist_categories=("Ll", "Lu", "Nd"),
        whitelist_characters="-_@/.",
    ),
    min_size=1,
    max_size=50,
).filter(lambda s: s.strip() and not s.startswith(".") and not s.startswith("_"))

# Strategy for a simple numeric version string (e.g. "1.2.3")
numeric_version = st.builds(
    lambda parts: ".".join(str(p) for p in parts),
    parts=st.lists(
        st.integers(min_value=0, max_value=999),
        min_size=1,
        max_size=4,
    ),
)

# Strategy for a valid package.json dict with at least one dependency section
valid_package_json = st.fixed_dictionaries(
    {},
    optional={
        "dependencies": st.dictionaries(
            keys=package_name,
            values=numeric_version,
            min_size=0,
            max_size=10,
        ),
        "devDependencies": st.dictionaries(
            keys=package_name,
            values=numeric_version,
            min_size=0,
            max_size=10,
        ),
    },
).filter(
    lambda pkg: (
        bool(pkg.get("dependencies")) or bool(pkg.get("devDependencies"))
    )
)


# ---------------------------------------------------------------------------
# Property 1: Missing package.json yields no CVE queries
# Validates: Requirements 3.4
# ---------------------------------------------------------------------------


class TestProperty1MissingPackageJsonYieldsNoCVEQueries:
    """
    **Property 1: Missing package.json yields no CVE queries**

    For all PR file lists that do not contain `package.json`,
    `parse_package_json` returns an empty list.

    Validates: Requirements 3.4
    """

    @given(files=files_without_package_json)
    @settings(max_examples=100)
    def test_no_package_json_returns_empty_list(self, files: list[dict]) -> None:
        """When no file has filename == 'package.json', parse_package_json returns []."""
        mock_coral = MagicMock()

        result = parse_package_json(
            files=files,
            coral=mock_coral,
            pr_number=1,
            owner="test-owner",
            repo="test-repo",
        )

        assert result == [], (
            f"Expected empty list when no package.json in files, got {result!r}"
        )

    @given(files=files_without_package_json)
    @settings(max_examples=100)
    def test_no_package_json_coral_query_never_called(self, files: list[dict]) -> None:
        """When no package.json is present, CoralClient.query is never called."""
        mock_coral = MagicMock()

        parse_package_json(
            files=files,
            coral=mock_coral,
            pr_number=1,
            owner="test-owner",
            repo="test-repo",
        )

        mock_coral.query.assert_not_called()


# ---------------------------------------------------------------------------
# Property 8: Dependency parsing extracts non-empty tuples
# Validates: Requirements 3.1
# ---------------------------------------------------------------------------


class TestProperty8DependencyParsingExtractsNonEmptyTuples:
    """
    **Property 8: Dependency parsing extracts non-empty tuples**

    For any valid `package.json` content, `parse_package_json` returns only
    `(name, version)` tuples where both elements are non-empty strings.

    Validates: Requirements 3.1
    """

    @given(pkg=valid_package_json)
    @settings(max_examples=100)
    def test_all_returned_tuples_have_non_empty_name_and_version(
        self, pkg: dict
    ) -> None:
        """Every (name, version) tuple returned has non-empty name and version strings."""
        content_str = json.dumps(pkg)

        mock_coral = MagicMock()
        mock_coral.query.return_value = [{"content": content_str}]

        files = [{"filename": "package.json"}]

        result = parse_package_json(
            files=files,
            coral=mock_coral,
            pr_number=42,
            owner="test-owner",
            repo="test-repo",
        )

        assert isinstance(result, list), (
            f"Expected list, got {type(result)!r}"
        )

        for item in result:
            assert isinstance(item, tuple) and len(item) == 2, (
                f"Expected 2-tuple, got {item!r}"
            )
            name, version = item
            assert isinstance(name, str) and name, (
                f"Tuple name is empty or not a string: {name!r}"
            )
            assert isinstance(version, str) and version, (
                f"Tuple version is empty or not a string: {version!r}"
            )

    @given(pkg=valid_package_json)
    @settings(max_examples=100)
    def test_returned_tuples_are_subsets_of_package_json_entries(
        self, pkg: dict
    ) -> None:
        """Every returned (name, version) pair originates from the package.json content."""
        content_str = json.dumps(pkg)

        mock_coral = MagicMock()
        mock_coral.query.return_value = [{"content": content_str}]

        files = [{"filename": "package.json"}]

        result = parse_package_json(
            files=files,
            coral=mock_coral,
            pr_number=42,
            owner="test-owner",
            repo="test-repo",
        )

        # Collect all declared dependency names from the package.json
        all_declared_names: set[str] = set()
        for section in ("dependencies", "devDependencies"):
            section_data = pkg.get(section)
            if isinstance(section_data, dict):
                all_declared_names.update(section_data.keys())

        for name, _version in result:
            assert name in all_declared_names, (
                f"Returned name {name!r} not found in package.json dependencies"
            )
