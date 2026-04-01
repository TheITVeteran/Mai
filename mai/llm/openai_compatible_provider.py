"""OpenAI-style ``/v1/chat/completions`` client (ollama, vLLM, hosted APIs)."""

from __future__ import annotations

import logging
from typing import Any, Optional

import requests

from mai.llm.types import ChatParams

logger = logging.getLogger(__name__)


def _extract_openai_message_text(data: dict[str, Any]) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("OpenAI-style response missing choices[]")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("OpenAI-style choice must be an object")
    msg = first.get("message")
    if isinstance(msg, dict) and msg.get("content") is not None:
        return str(msg["content"]).strip()
    # Some servers expose legacy text field
    if first.get("text") is not None:
        return str(first["text"]).strip()
    raise ValueError("OpenAI-style response missing message.content")


class OpenAICompatibleProvider:
    """POST to a full chat-completions URL (path e.g. ``/v1/chat/completions``)."""

    def __init__(
        self,
        *,
        api_url: str,
        default_model: str,
        api_key: Optional[str] = None,
    ) -> None:
        self.api_url = (api_url or "").strip()
        self.default_model = default_model
        self.api_key = (api_key or "").strip() or None

    @property
    def kind(self) -> str:
        return "openai_compatible"

    def is_available(self) -> bool:
        return bool(self.api_url)

    def complete(self, params: ChatParams, *, timeout: float) -> str:
        messages: list[dict[str, str]] = []
        if params.use_system_prompt_field and params.system_prompt:
            messages.append({"role": "system", "content": params.system_prompt})
            messages.append({"role": "user", "content": params.user_prompt})
        elif params.system_prompt:
            merged = params.system_prompt + "\n\n" + params.user_prompt
            messages.append(
                {
                    "role": "user",
                    "content": merged.lstrip(),
                }
            )
        else:
            messages.append({"role": "user", "content": params.user_prompt})

        body: dict[str, Any] = {
            "model": params.model or self.default_model,
            "messages": messages,
        }
        if params.max_output_tokens:
            body["max_tokens"] = params.max_output_tokens
        if params.temperature is not None:
            body["temperature"] = params.temperature

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        logger.debug(
            "OpenAI-compatible POST %s model=%r",
            self.api_url,
            body.get("model"),
        )
        resp = requests.post(self.api_url, json=body, headers=headers, timeout=timeout)
        resp.raise_for_status()
        raw = resp.json()
        if not isinstance(raw, dict):
            raise ValueError("OpenAI-style response JSON must be an object")
        return _extract_openai_message_text(raw)
