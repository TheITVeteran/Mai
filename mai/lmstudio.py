"""LM Studio `/api/v1/chat` response parsing."""

from __future__ import annotations

from typing import Any


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
