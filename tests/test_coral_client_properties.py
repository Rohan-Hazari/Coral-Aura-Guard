"""
Property-based tests for CoralClient in commands/__init__.py.
Updated for Async CLI implementation (Hypothesis compatible).
"""

from __future__ import annotations

import json
import logging
import time
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from commands import CoralClient

# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

non_empty_sql = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    min_size=1,
    max_size=500,
).filter(lambda s: s.strip())

sql_param_key = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="_"),
    min_size=1,
    max_size=30,
).filter(lambda s: s[0].isalpha() or s[0] == "_")

sql_param_value = st.one_of(
    st.integers(min_value=-10_000, max_value=10_000),
    st.text(min_size=0, max_size=100),
    st.none(),
)

params_dict = st.dictionaries(
    keys=sql_param_key,
    values=sql_param_value,
    min_size=0,
    max_size=10,
)

class TestCoralClientProperties:
    """
    Property-based tests for CoralClient (Async CLI version).
    Uses asyncio.run to be compatible with Hypothesis.
    """

    @given(sql=non_empty_sql)
    @settings(max_examples=20)
    def test_query_latency_recorded(self, sql: str) -> None:
        """Property: elapsed_ms is always recorded in the result."""
        async def run():
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (json.dumps({"rows": []}).encode(), b"")
            mock_process.returncode = 0

            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                client = CoralClient("coral")
                result = await client.query(sql)
                assert "elapsed_ms" in result
                assert isinstance(result["elapsed_ms"], int)
                assert result["row_count"] == 0
        
        asyncio.run(run())

    @given(sql=non_empty_sql, params=params_dict)
    @settings(max_examples=20)
    def test_bind_variable_substitution(self, sql: str, params: dict) -> None:
        """Property: parameters are substituted into the SQL string (demo implementation)."""
        async def run():
            # Ensure we don't have empty params for this specific test if we want to check substitution
            test_sql = sql
            test_params = params
            if not test_params:
                test_params = {"test_key": "test_val"}
                test_sql = "SELECT * FROM table WHERE col = :test_key"

            mock_process = AsyncMock()
            mock_process.communicate.return_value = (json.dumps({"rows": []}).encode(), b"")
            mock_process.returncode = 0

            with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
                client = CoralClient("coral")
                await client.query(test_sql, test_params)
                
                # Get the SQL passed to the exec call
                args, kwargs = mock_exec.call_args
                final_sql = args[4] # 'coral', 'sql', '--format', 'json', final_sql
                
                for k, v in test_params.items():
                    if f":{k}" in test_sql and v is not None:
                        if isinstance(v, str):
                            assert v in final_sql
                        else:
                            assert str(v) in final_sql
        
        asyncio.run(run())

    @given(sql=non_empty_sql)
    @settings(max_examples=10)
    def test_error_handling_non_zero_exit(self, sql: str) -> None:
        """Property: CoralQueryError is raised on non-zero exit code."""
        async def run():
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"Some error from CLI")
            mock_process.returncode = 1

            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                client = CoralClient("coral")
                from commands import CoralQueryError
                with pytest.raises(CoralQueryError) as exc:
                    await client.query(sql)
                assert "Coral CLI Error" in str(exc.value)
        
        asyncio.run(run())

    @given(sql=non_empty_sql)
    @settings(max_examples=10)
    def test_timeout_handling(self, sql: str) -> None:
        """Property: CoralQueryError is raised on timeout."""
        async def run():
            with patch("asyncio.create_subprocess_exec") as mock_exec:
                mock_process = AsyncMock()
                mock_exec.return_value = mock_process
                # Mock wait_for to raise TimeoutError
                with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
                    client = CoralClient("coral")
                    from commands import CoralQueryError
                    with pytest.raises(CoralQueryError) as exc:
                        await client.query(sql)
                    assert "timed out" in str(exc.value)
                    assert mock_process.kill.called
        
        asyncio.run(run())
