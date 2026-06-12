"""Provider-agnostic LLM client for FlowDesk."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


class LLMError(RuntimeError):
    """Base error for configured LLM calls."""


class LLMConfigError(LLMError):
    """Raised when the selected provider is missing required config."""


class LLMProviderError(LLMError):
    """Raised when the selected provider call fails."""


class LLMResponseError(LLMError):
    """Raised when a provider returns empty or invalid JSON."""


def call_llm(prompt: str, response_schema: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call the configured LLM provider and return a parsed dictionary.

    Required environment:
    - ``LLM_PROVIDER=gemini|openai|openrouter|ollama``
    - ``LLM_API_KEY`` for Gemini/OpenAI/OpenRouter
    - ``LLM_MODEL`` for all providers
    - ``OLLAMA_HOST`` for Ollama, defaulting to localhost
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    llm_prompt = _schema_prompt(prompt, response_schema)
    if provider == "gemini":
        text = _call_gemini(llm_prompt, response_schema)
    elif provider == "openai":
        text = _call_openai(llm_prompt, response_schema)
    elif provider == "openrouter":
        text = _call_openrouter(llm_prompt, response_schema)
    elif provider == "ollama":
        text = _call_ollama(llm_prompt, response_schema)
    else:
        raise LLMConfigError("LLM_PROVIDER must be one of: gemini, openai, openrouter, ollama.")

    if not text.strip():
        raise LLMResponseError(f"{provider} returned an empty response.")

    if response_schema is None:
        return {"text": text}

    return _parse_json_response(text)


def _call_gemini(prompt: str, response_schema: dict[str, Any] | None) -> str:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "gemini-2.0-flash").strip()
    if not api_key:
        raise LLMConfigError("LLM_API_KEY is required when LLM_PROVIDER=gemini.")
    if not model:
        raise LLMConfigError("LLM_MODEL is required when LLM_PROVIDER=gemini.")

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(temperature=0.1)
        if response_schema:
            config.response_mime_type = "application/json"
            config.response_schema = _upper_schema_types(response_schema)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )
        return response.text or ""
    except Exception as exc:  # pragma: no cover - provider details vary
        raise LLMProviderError(_redact(str(exc), api_key)) from exc


def _call_openai(prompt: str, response_schema: dict[str, Any] | None) -> str:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "gpt-4.1-mini").strip()
    if not api_key:
        raise LLMConfigError("LLM_API_KEY is required when LLM_PROVIDER=openai.")
    if not model:
        raise LLMConfigError("LLM_MODEL is required when LLM_PROVIDER=openai.")

    messages = [
        {
            "role": "system",
            "content": "Return only valid JSON when a schema is requested.",
        },
        {"role": "user", "content": prompt},
    ]
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
    }
    if response_schema:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "flowdesk_response",
                "schema": _lower_schema_types(response_schema),
                "strict": True,
            },
        }

    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=40.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"] or ""
    except Exception as exc:
        raise LLMProviderError(_redact(str(exc), api_key)) from exc


def _call_openrouter(prompt: str, response_schema: dict[str, Any] | None) -> str:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free").strip()
    if not api_key:
        raise LLMConfigError("LLM_API_KEY is required when LLM_PROVIDER=openrouter.")
    if not model:
        raise LLMConfigError("LLM_MODEL is required when LLM_PROVIDER=openrouter.")

    messages = [
        {"role": "user", "content": prompt},
    ]
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
    }
    if response_schema:
        payload["response_format"] = {"type": "json_object"}

    try:
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/qonstellations/flowdesk",
                "X-Title": "FlowDesk",
            },
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"] or ""
    except Exception as exc:
        raise LLMProviderError(_redact(str(exc), api_key)) from exc


def _call_ollama(prompt: str, response_schema: dict[str, Any] | None) -> str:
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip().rstrip("/")
    model = os.getenv("LLM_MODEL", os.getenv("OLLAMA_MODEL", "llama3")).strip()
    timeout_seconds = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
    if not model:
        raise LLMConfigError("LLM_MODEL is required when LLM_PROVIDER=ollama.")

    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.1},
    }
    if response_schema:
        payload["format"] = _lower_schema_types(response_schema)

    try:
        response = httpx.post(f"{host}/api/chat", json=payload, timeout=timeout_seconds)
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")
    except Exception as exc:
        raise LLMProviderError(str(exc)) from exc


def _parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    if not cleaned.startswith("{"):
        extracted = _extract_json_object(cleaned)
        if extracted:
            cleaned = extracted
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LLMResponseError(f"LLM returned invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise LLMResponseError("LLM JSON response must be an object.")
    return value


def _schema_prompt(prompt: str, response_schema: dict[str, Any] | None) -> str:
    if response_schema is None:
        return prompt
    return f"""{prompt}

Return exactly one valid JSON object.
Do not include markdown fences, commentary, prose, or explanations outside JSON.
The JSON object must satisfy this JSON Schema:
{json.dumps(_lower_schema_types(response_schema), separators=(",", ":"))}
"""


def _extract_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if escape:
            escape = False
            continue
        if char == "\\" and in_string:
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def _lower_schema_types(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: (val.lower() if key == "type" and isinstance(val, str) else _lower_schema_types(val))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [_lower_schema_types(item) for item in value]
    return value


def _upper_schema_types(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: (val.upper() if key == "type" and isinstance(val, str) else _upper_schema_types(val))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [_upper_schema_types(item) for item in value]
    return value


def _redact(message: str, secret: str) -> str:
    return message.replace(secret, "***REDACTED***") if secret else message


def call_gemini(prompt: str, response_schema: dict[str, Any] | None = None) -> dict[str, Any]:
    """Backward-compatible alias. New code should call ``call_llm``."""
    return call_llm(prompt, response_schema=response_schema)
