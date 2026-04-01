"""LM Studio ``/api/v1/chat`` backend (primary default)."""

from __future__ import annotations

import logging
from typing import Any

from mai.llm.types import ChatParams
from mai.lmstudio import extract_assistant_text, post_chat

logger = logging.getLogger(__name__)


class LMStudioProvider:
    """POST JSON to LM Studio; uses ``mai.lmstudio`` wire format."""

    def __init__(self, *, api_url: str, default_model: str) -> None:
        self.api_url = (api_url or "").strip()
        self.default_model = default_model

    @property
    def kind(self) -> str:
        return "lmstudio"

    def is_available(self) -> bool:
        return bool(self.api_url)

    def complete(self, params: ChatParams, *, timeout: float) -> str:
        body: dict[str, Any] = {
            "model": params.model or self.default_model,
            "max_output_tokens": params.max_output_tokens,
        }
        if params.repeat_penalty is not None:
            body["repeat_penalty"] = params.repeat_penalty
        if params.temperature is not None:
            body["temperature"] = params.temperature

        if params.use_system_prompt_field and params.system_prompt:
            body["system_prompt"] = params.system_prompt
            body["input"] = params.user_prompt
        else:
            if params.system_prompt:
                merged = params.system_prompt + "\n\n" + params.user_prompt
                body["input"] = merged.lstrip()
            else:
                body["input"] = params.user_prompt

        data = post_chat(self.api_url, body, timeout=timeout)
        return extract_assistant_text(data)
