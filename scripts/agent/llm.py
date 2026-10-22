"""OpenAI-compatible chat client for drafting test updates."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def call_chat(
    *,
    system: str,
    user: str,
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    timeout: int = 120,
) -> str:
    base = (base_url or os.environ.get("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip(
        "/"
    )
    model_name = model or os.environ.get("LLM_MODEL") or "gpt-4o-mini"
    key = api_key if api_key is not None else os.environ.get("LLM_API_KEY", "")
    if not key:
        raise RuntimeError("LLM_API_KEY is not set")

    payload = {
        "model": model_name,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    request = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM HTTP {exc.code}: {detail}") from exc

    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"unexpected LLM response: {body!r}") from exc


def parse_json_content(content: str) -> Any:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)
