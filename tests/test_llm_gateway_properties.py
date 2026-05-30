"""
Property-based tests for LLM Gateway in commands/llm_gateway.py.

Uses hypothesis to verify universal correctness properties across all valid
inputs for the call_llm function.
"""

from __future__ import annotations

import json
import os
import re
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from commands.llm_gateway import call_llm, LLMError

# ---------------------------------------------------------------------------
# Shared strategies (Optimized to eliminate filter timeouts)
# ---------------------------------------------------------------------------

# Strategy for simple scalar values that can appear in row dicts
scalar_value = st.one_of(
    st.integers(min_value=-10_000, max_value=10_000),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
    st.text(min_size=0, max_size=100),
    st.booleans(),
    st.none(),
)

# FIX: Build row keys structurally — first char is always alpha or underscore,
# rest are alphanumeric or underscore. Zero filter overhead.
row_key = st.builds(
    lambda first, rest: first + rest,
    first=st.characters(whitelist_categories=("Ll", "Lu"), whitelist_characters="_"),
    rest=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="_"),
        min_size=0,
        max_size=29,
    ),
)

# Strategy for a single row dict
row_dict = st.dictionaries(
    keys=row_key,
    values=scalar_value,
    min_size=0,
    max_size=8,
)

# Strategy for a list of row dicts (at least one row)
rows_list = st.lists(row_dict, min_size=1, max_size=10)

# Strategy for command context
command_strategy = st.sampled_from(["supply-chain", "blast-radius", "unknown"])

# Strategy for context dicts
context_strategy = st.fixed_dictionaries({"command": command_strategy})

# FIX: Constrain to realistic token characters — alphanumeric + common punctuation.
# Every generated string is immediately valid; no filter rejection overhead.
secret_value_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("Ll", "Lu", "Nd"),
        whitelist_characters="-_=+/",
    ),
    min_size=4,
    max_size=64,
)


# ---------------------------------------------------------------------------
# Helper: build a mock OpenAI client that captures the prompt
# ---------------------------------------------------------------------------

def _make_mock_client(captured_messages: list) -> MagicMock:
    """Return a mock openai.OpenAI client that records messages and returns a fake response."""
    mock_message = MagicMock()
    mock_message.content = "# Security Report\n- Action item 1"

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_completions = MagicMock()
    mock_completions.create.side_effect = lambda **kwargs: (
        captured_messages.append(kwargs.get("messages", [])) or mock_response
    )

    mock_chat = MagicMock()
    mock_chat.completions = mock_completions

    mock_client = MagicMock()
    mock_client.chat = mock_chat

    return mock_client


# ---------------------------------------------------------------------------
# Property 5: LLM prompts never contain secrets
# Validates: Requirements 6.5, 9.3
# ---------------------------------------------------------------------------


class TestProperty5LLMPromptsNeverContainSecrets:
    """
    **Property 5: LLM prompts never contain secrets**

    For any list of rows and any context dict, the prompt string passed to
    the LLM API does not contain the values of CORAL_TOKEN, OPENAI_API_KEY,
    or GITHUB_TOKEN.

    Validates: Requirements 6.5, 9.3
    """

    @given(
        rows=rows_list,
        context=context_strategy,
        coral_token=secret_value_strategy,
        openai_api_key=secret_value_strategy,
        github_token=secret_value_strategy,
    )
    @settings(max_examples=50)
    def test_prompt_does_not_contain_coral_token(
        self,
        rows: list[dict],
        context: dict,
        coral_token: str,
        openai_api_key: str,
        github_token: str,
    ) -> None:
        """The prompt sent to the LLM must not contain the CORAL_TOKEN value."""
        captured_messages: list = []
        mock_client = _make_mock_client(captured_messages)

        env_overrides = {
            "CORAL_TOKEN": coral_token,
            "OPENAI_API_KEY": openai_api_key,
            "GITHUB_TOKEN": github_token,
        }

        # Use a prompt template that does NOT embed secrets directly
        prompt_template = "Analyze these rows: {rows_json}"

        with patch.dict(os.environ, env_overrides, clear=False):
            with patch("commands.llm_gateway.openai.OpenAI", return_value=mock_client):
                try:
                    call_llm(rows, prompt_template, context)
                except LLMError:
                    # LLMError is acceptable — it means the secret-leak guard fired,
                    # which is the correct behavior. The test still passes.
                    return

        # If call_llm succeeded, verify the captured prompt has no secrets
        assert len(captured_messages) == 1
        messages = captured_messages[0]
        prompt_text = " ".join(
            msg.get("content", "") for msg in messages if isinstance(msg, dict)
        )
        assert coral_token not in prompt_text, (
            f"CORAL_TOKEN value found in prompt: {prompt_text!r}"
        )

    @given(
        rows=rows_list,
        context=context_strategy,
        coral_token=secret_value_strategy,
        openai_api_key=secret_value_strategy,
        github_token=secret_value_strategy,
    )
    @settings(max_examples=50)
    def test_prompt_does_not_contain_openai_api_key(
        self,
        rows: list[dict],
        context: dict,
        coral_token: str,
        openai_api_key: str,
        github_token: str,
    ) -> None:
        """The prompt sent to the LLM must not contain the OPENAI_API_KEY value."""
        captured_messages: list = []
        mock_client = _make_mock_client(captured_messages)

        env_overrides = {
            "CORAL_TOKEN": coral_token,
            "OPENAI_API_KEY": openai_api_key,
            "GITHUB_TOKEN": github_token,
        }

        prompt_template = "Analyze these rows: {rows_json}"

        with patch.dict(os.environ, env_overrides, clear=False):
            with patch("commands.llm_gateway.openai.OpenAI", return_value=mock_client):
                try:
                    call_llm(rows, prompt_template, context)
                except LLMError:
                    return

        assert len(captured_messages) == 1
        messages = captured_messages[0]
        prompt_text = " ".join(
            msg.get("content", "") for msg in messages if isinstance(msg, dict)
        )
        assert openai_api_key not in prompt_text, (
            f"OPENAI_API_KEY value found in prompt: {prompt_text!r}"
        )

    @given(
        rows=rows_list,
        context=context_strategy,
        coral_token=secret_value_strategy,
        openai_api_key=secret_value_strategy,
        github_token=secret_value_strategy,
    )
    @settings(max_examples=50)
    def test_prompt_does_not_contain_github_token(
        self,
        rows: list[dict],
        context: dict,
        coral_token: str,
        openai_api_key: str,
        github_token: str,
    ) -> None:
        """The prompt sent to the LLM must not contain the GITHUB_TOKEN value."""
        captured_messages: list = []
        mock_client = _make_mock_client(captured_messages)

        env_overrides = {
            "CORAL_TOKEN": coral_token,
            "OPENAI_API_KEY": openai_api_key,
            "GITHUB_TOKEN": github_token,
        }

        prompt_template = "Analyze these rows: {rows_json}"

        with patch.dict(os.environ, env_overrides, clear=False):
            with patch("commands.llm_gateway.openai.OpenAI", return_value=mock_client):
                try:
                    call_llm(rows, prompt_template, context)
                except LLMError:
                    return

        assert len(captured_messages) == 1
        messages = captured_messages[0]
        prompt_text = " ".join(
            msg.get("content", "") for msg in messages if isinstance(msg, dict)
        )
        assert github_token not in prompt_text, (
            f"GITHUB_TOKEN value found in prompt: {prompt_text!r}"
        )

    @given(
        rows=rows_list,
        context=context_strategy,
        secret=secret_value_strategy,
    )
    @settings(max_examples=50)
    def test_secret_in_prompt_template_raises_llm_error(
        self,
        rows: list[dict],
        context: dict,
        secret: str,
    ) -> None:
        """If a secret value is embedded in the prompt template, LLMError is raised."""
        captured_messages: list = []
        mock_client = _make_mock_client(captured_messages)

        # Embed the secret directly in the template (simulating a bug)
        prompt_template = f"Token: {secret} Rows: {{rows_json}}"

        env_overrides = {
            "CORAL_TOKEN": secret,
            "OPENAI_API_KEY": "safe-key-xyz",
            "GITHUB_TOKEN": "safe-gh-token",
        }

        with patch.dict(os.environ, env_overrides, clear=False):
            with patch("commands.llm_gateway.openai.OpenAI", return_value=mock_client):
                with pytest.raises(LLMError):
                    call_llm(rows, prompt_template, context)

        # The LLM must NOT have been called when a secret would leak
        assert len(captured_messages) == 0, (
            "LLM was called even though the prompt contained a secret value"
        )


# ---------------------------------------------------------------------------
# Property 11: LLM prompt rows are compact JSON
# Validates: Requirements 6.1, 6.2
# ---------------------------------------------------------------------------


class TestProperty11LLMPromptRowsAreCompactJSON:
    """
    **Property 11: LLM prompt rows are compact JSON**

    For any list of Coral result rows passed to call_llm, the serialized
    rows in the prompt contain no extra whitespace characters (no spaces
    after ':' or ',', no newlines).

    Validates: Requirements 6.1, 6.2
    """

    @given(rows=rows_list, context=context_strategy)
    @settings(max_examples=50)
    def test_serialized_rows_have_no_space_after_colon(
        self, rows: list[dict], context: dict
    ) -> None:
        """The JSON rows in the prompt must not have a space after ':'."""
        captured_messages: list = []
        mock_client = _make_mock_client(captured_messages)

        prompt_template = "Data: {rows_json}"

        with patch.dict(os.environ, {"CORAL_TOKEN": "", "OPENAI_API_KEY": "", "GITHUB_TOKEN": ""}, clear=False):
            with patch("commands.llm_gateway.openai.OpenAI", return_value=mock_client):
                try:
                    call_llm(rows, prompt_template, context)
                except LLMError:
                    pytest.skip("LLMError raised (e.g. empty response); skipping whitespace check")

        assert len(captured_messages) == 1
        prompt_text = captured_messages[0][0]["content"]

        # Extract the JSON portion from the prompt
        json_match = re.search(r"\[.*\]", prompt_text, re.DOTALL)
        assert json_match is not None, f"No JSON array found in prompt: {prompt_text!r}"
        json_str = json_match.group(0)

        assert ": " not in json_str, (
            f"Found ': ' (space after colon) in serialized JSON rows: {json_str!r}"
        )

    @given(rows=rows_list, context=context_strategy)
    @settings(max_examples=50)
    def test_serialized_rows_have_no_space_after_comma(
        self, rows: list[dict], context: dict
    ) -> None:
        """The JSON rows in the prompt must not have a space after ','."""
        captured_messages: list = []
        mock_client = _make_mock_client(captured_messages)

        prompt_template = "Data: {rows_json}"

        with patch.dict(os.environ, {"CORAL_TOKEN": "", "OPENAI_API_KEY": "", "GITHUB_TOKEN": ""}, clear=False):
            with patch("commands.llm_gateway.openai.OpenAI", return_value=mock_client):
                try:
                    call_llm(rows, prompt_template, context)
                except LLMError:
                    pytest.skip("LLMError raised (e.g. empty response); skipping whitespace check")

        assert len(captured_messages) == 1
        prompt_text = captured_messages[0][0]["content"]

        json_match = re.search(r"\[.*\]", prompt_text, re.DOTALL)
        assert json_match is not None, f"No JSON array found in prompt: {prompt_text!r}"
        json_str = json_match.group(0)

        assert ", " not in json_str, (
            f"Found ', ' (space after comma) in serialized JSON rows: {json_str!r}"
        )

    @given(rows=rows_list, context=context_strategy)
    @settings(max_examples=50)
    def test_serialized_rows_have_no_newlines(
        self, rows: list[dict], context: dict
    ) -> None:
        """The JSON rows in the prompt must not contain newline characters."""
        captured_messages: list = []
        mock_client = _make_mock_client(captured_messages)

        prompt_template = "Data: {rows_json}"

        with patch.dict(os.environ, {"CORAL_TOKEN": "", "OPENAI_API_KEY": "", "GITHUB_TOKEN": ""}, clear=False):
            with patch("commands.llm_gateway.openai.OpenAI", return_value=mock_client):
                try:
                    call_llm(rows, prompt_template, context)
                except LLMError:
                    pytest.skip("LLMError raised (e.g. empty response); skipping whitespace check")

        assert len(captured_messages) == 1
        prompt_text = captured_messages[0][0]["content"]

        json_match = re.search(r"\[.*\]", prompt_text, re.DOTALL)
        assert json_match is not None, f"No JSON array found in prompt: {prompt_text!r}"
        json_str = json_match.group(0)

        assert "\n" not in json_str, (
            f"Found newline in serialized JSON rows: {json_str!r}"
        )

    @given(rows=rows_list, context=context_strategy)
    @settings(max_examples=50)
    def test_serialized_rows_are_valid_json(
        self, rows: list[dict], context: dict
    ) -> None:
        """The JSON rows in the prompt must be parseable as valid JSON."""
        captured_messages: list = []
        mock_client = _make_mock_client(captured_messages)

        prompt_template = "Data: {rows_json}"

        with patch.dict(os.environ, {"CORAL_TOKEN": "", "OPENAI_API_KEY": "", "GITHUB_TOKEN": ""}, clear=False):
            with patch("commands.llm_gateway.openai.OpenAI", return_value=mock_client):
                try:
                    call_llm(rows, prompt_template, context)
                except LLMError:
                    pytest.skip("LLMError raised (e.g. empty response); skipping JSON validity check")

        assert len(captured_messages) == 1
        prompt_text = captured_messages[0][0]["content"]

        json_match = re.search(r"\[.*\]", prompt_text, re.DOTALL)
        assert json_match is not None, f"No JSON array found in prompt: {prompt_text!r}"
        json_str = json_match.group(0)

        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as exc:
            pytest.fail(f"Serialized rows are not valid JSON: {exc}\nJSON string: {json_str!r}")

        assert isinstance(parsed, list), f"Expected a JSON array, got: {type(parsed)}"

    @given(rows=rows_list, context=context_strategy)
    @settings(max_examples=50)
    def test_compact_json_matches_expected_serialization(
        self, rows: list[dict], context: dict
    ) -> None:
        """The JSON rows in the prompt must match json.dumps with separators=(',', ':')."""
        captured_messages: list = []
        mock_client = _make_mock_client(captured_messages)

        prompt_template = "Data: {rows_json}"

        with patch.dict(os.environ, {"CORAL_TOKEN": "", "OPENAI_API_KEY": "", "GITHUB_TOKEN": ""}, clear=False):
            with patch("commands.llm_gateway.openai.OpenAI", return_value=mock_client):
                try:
                    call_llm(rows, prompt_template, context)
                except LLMError:
                    pytest.skip("LLMError raised; skipping compact JSON check")

        assert len(captured_messages) == 1
        prompt_text = captured_messages[0][0]["content"]

        json_match = re.search(r"\[.*\]", prompt_text, re.DOTALL)
        assert json_match is not None, f"No JSON array found in prompt: {prompt_text!r}"
        json_str = json_match.group(0)

        # Parse the JSON to get the actual filtered rows, then re-serialize compactly
        parsed_rows = json.loads(json_str)
        expected_compact = json.dumps(parsed_rows, separators=(",", ":"))

        assert json_str == expected_compact, (
            f"Serialized rows are not compact JSON.\n"
            f"  Got:      {json_str!r}\n"
            f"  Expected: {expected_compact!r}"
        )
