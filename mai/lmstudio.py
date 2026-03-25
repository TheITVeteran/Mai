"""LM Studio `/api/v1/chat` HTTP client and response parsing."""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


def post_chat(
    api_url: str,
    body: dict[str, Any],
    *,
    timeout: float,
) -> dict[str, Any]:
    """
    POST JSON to LM Studio chat API; return response body as a dict.

    Raises ``requests.HTTPError`` on non-success status.
    """
    logger.debug("LM Studio POST %s model=%r", api_url, body.get("model"))
    response = requests.post(api_url, json=body, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("LM Studio response JSON must be an object")
    return data


def extract_assistant_text(data: dict[str, Any]) -> str:
    """
    Use the last `output` item with type ``message`` (LM Studio can return
    reasoning / tool items before the final assistant text).

    Falls back to ``output[0].content`` for older shapes.
    """
    out = data.get("output")
    if not isinstance(out, list) or not out:
        raise ValueError("LM Studio response missing output[]")

    messages: list[str] = []
    for item in out:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "message":
            content = item.get("content")
            if content is not None and str(content).strip():
                messages.append(str(content).strip())

    if messages:
        return messages[-1]

    first = out[0]
    if isinstance(first, dict) and first.get("content") is not None:
        return str(first["content"]).strip()

    raise ValueError("LM Studio output contained no assistant message content")
