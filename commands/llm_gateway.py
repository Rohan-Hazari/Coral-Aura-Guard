"""
LLM Gateway — commands/llm_gateway.py

Selects the LLM backend from environment variables:
    MODEL_PROVIDER = openai | google
    MODEL_API_KEY  = your API key
    MODEL_NAME     = model name (e.g. gpt-4.1-mini, gemini-1.5-flash)
"""

from __future__ import annotations

import json
import logging
import os
import sys

logger = logging.getLogger(__name__)

if not logger.handlers and not logging.root.handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setLevel(logging.WARNING)
    logger.addHandler(_handler)
    logger.setLevel(logging.WARNING)

# Column allow-lists per command
_SUPPLY_CHAIN_COLUMNS = frozenset({"cve_id", "summary", "severity", "filename"})
_BLAST_RADIUS_COLUMNS = frozenset({"downstream_repo", "active_pr", "developer"})

# Secret env-var names whose values must never appear in prompts
_SECRET_ENV_VARS = (
    "MODEL_API_KEY",
    "GITHUB_TOKEN",
    "CORAL_CONNECTION_URL",
    "SLACK_BOT_TOKEN",
    "NOTION_TOKEN",
)

_DEFAULT_TIMEOUT = 30


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class LLMError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _filter_rows(rows: list[dict], command: str) -> list[dict]:
    if command == "supply-chain":
        allowed = _SUPPLY_CHAIN_COLUMNS
    elif command == "blast-radius":
        allowed = _BLAST_RADIUS_COLUMNS
    else:
        # org-scan and others pre-filter before calling — pass through
        return [dict(row) for row in rows]
    return [{k: v for k, v in row.items() if k in allowed} for row in rows]


def _assert_no_secrets(prompt: str) -> None:
    for var_name in _SECRET_ENV_VARS:
        secret_value = os.environ.get(var_name, "")
        if secret_value and secret_value in prompt:
            raise LLMError(
                f"Secret value of {var_name!r} must not appear in the LLM prompt."
            )


def _call_openai(prompt: str, model: str, api_key: str, timeout: float) -> str:
    try:
        import openai
    except ImportError:
        raise LLMError("openai package not installed. Run: pip install openai")

    client = openai.OpenAI(api_key=api_key, timeout=timeout)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
    except openai.APITimeoutError as exc:
        raise LLMError(f"OpenAI timed out after {timeout}s: {exc}") from exc
    except openai.APIStatusError as exc:
        raise LLMError(f"OpenAI error {exc.status_code}: {exc.message}") from exc
    except openai.APIError as exc:
        raise LLMError(f"OpenAI API error: {exc}") from exc

    content = response.choices[0].message.content or ""
    if not content.strip():
        raise LLMError("OpenAI returned an empty response.")
    return content


def _call_google(prompt: str, model: str, api_key: str, timeout: float) -> str:
    try:
        import google.generativeai as genai
    except ImportError:
        raise LLMError(
            "google-generativeai not installed. Run: pip install google-generativeai"
        )

    genai.configure(api_key=api_key)
    try:
        gemini_model = genai.GenerativeModel(model)
        response = gemini_model.generate_content(prompt)
        content = response.text or ""
    except Exception as exc:
        raise LLMError(f"Gemini API error: {exc}") from exc

    if not content.strip():
        raise LLMError("Gemini returned an empty response.")
    return content


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def call_llm(rows: list[dict], prompt_template: str, context: dict) -> str:
    """Serialize rows as compact JSON, build the prompt, and call the LLM.

    Backend is selected from env vars:
        MODEL_PROVIDER = openai | google
        MODEL_API_KEY  = API key
        MODEL_NAME     = model name (optional, has sensible defaults)

    Args:
        rows: Coral result rows.
        prompt_template: String with a ``{rows_json}`` placeholder.
        context: Dict with ``command`` key and optional ``timeout``, ``model``.

    Returns:
        Non-empty LLM response string.

    Raises:
        LLMError: On API errors, timeouts, empty responses, or secret leaks.
    """
    provider = os.environ.get("MODEL_PROVIDER", "openai").lower().strip()
    api_key = os.environ.get("MODEL_API_KEY", "")
    timeout = float(context.get("timeout", _DEFAULT_TIMEOUT))
    command = context.get("command", "")

    # Default model names per provider
    default_models = {
        "openai": "gpt-4.1-mini",
        "google": "gemini-1.5-flash",
    }
    model = context.get("model") or os.environ.get("MODEL_NAME") or default_models.get(provider, "gpt-4.1-mini")

    if not api_key:
        raise LLMError("MODEL_API_KEY is not set.")

    # Filter columns, serialize compactly, build prompt
    filtered_rows = _filter_rows(rows, command)
    rows_json = json.dumps(filtered_rows, separators=(",", ":"))
    prompt = prompt_template.replace("{rows_json}", rows_json)

    _assert_no_secrets(prompt)

    logger.debug("Calling LLM provider=%s model=%s", provider, model)

    if provider == "google":
        return _call_google(prompt, model, api_key, timeout)
    elif provider == "openai":
        return _call_openai(prompt, model, api_key, timeout)
    else:
        raise LLMError(
            f"Unknown MODEL_PROVIDER={provider!r}. Use 'openai' or 'google'."
        )
