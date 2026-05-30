"""
Property-based tests for normalize_version in commands/supply_chain.py.

Uses hypothesis to verify universal correctness properties across all valid
and invalid inputs for the version normalization function.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from commands.supply_chain import normalize_version

# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

# Strategy for a valid numeric version string (e.g. "1", "1.2", "1.2.3")
numeric_version = st.builds(
    lambda parts: ".".join(str(p) for p in parts),
    parts=st.lists(
        st.integers(min_value=0, max_value=999),
        min_size=1,
        max_size=4,
    ),
)

# Range operators that should be stripped by normalize_version
RANGE_OPERATORS = ["^", "~", ">=", "<=", ">"]

# Strategy for a version string with a leading range operator
versioned_with_operator = st.builds(
    lambda op, ver: op + ver,
    op=st.sampled_from(RANGE_OPERATORS),
    ver=numeric_version,
)

# Strategy for arbitrary text strings (to test idempotency on all inputs)
arbitrary_version_string = st.one_of(
    st.text(max_size=50),                   # arbitrary strings
    numeric_version,                         # plain numeric versions
    versioned_with_operator,                 # operator-prefixed versions
    st.just("latest"),                       # non-numeric alias
    st.just("*"),                            # wildcard
    st.just(""),                             # empty string
    st.just("1.x"),                          # wildcard component
    st.just(">=1.0.0 <2.0.0"),              # compound range
    st.just("git+https://github.com/a/b"),  # non-registry reference
)


# ---------------------------------------------------------------------------
# Property 6: Version normalization is idempotent
# Validates: Requirements 3.3
# ---------------------------------------------------------------------------

class TestProperty6VersionNormalizationIdempotent:
    """
    **Property 6: Version normalization is idempotent**

    normalize(normalize(v)) == normalize(v) for any version string.

    Validates: Requirements 3.3
    """

    @given(version=arbitrary_version_string)
    def test_normalization_is_idempotent(self, version):
        """Applying normalize_version twice yields the same result as once."""
        first = normalize_version(version)
        # When first is None, normalize_version(None) should also return None
        second = normalize_version(first) if first is not None else None
        assert second == first, (
            f"Idempotency violated: normalize(normalize({version!r})) = {second!r} "
            f"but normalize({version!r}) = {first!r}"
        )


# ---------------------------------------------------------------------------
# Property 9: Version normalization strips range operators
# Validates: Requirements 3.2
# ---------------------------------------------------------------------------

class TestProperty9VersionNormalizationStripsRangeOperators:
    """
    **Property 9: Version normalization strips range operators**

    For any version string with a leading ^, ~, >=, <=, or >,
    normalize_version returns a string starting with a digit.

    Validates: Requirements 3.2
    """

    @given(version=versioned_with_operator)
    def test_strips_range_operator_returns_digit_start(self, version):
        """For any operator-prefixed numeric version, normalize_version returns a digit-starting string."""
        result = normalize_version(version)
        assert result is not None, (
            f"normalize_version({version!r}) returned None, expected a digit-starting string"
        )
        assert result[0].isdigit(), (
            f"normalize_version({version!r}) = {result!r}, expected result to start with a digit"
        )
