"""Instantiate the configured chat provider."""

from __future__ import annotations

import logging

from mai.config import (
    LLM_API_KEY,
    LLM_API_URL,
    LLM_MODEL,
    LLM_PROVIDER,
)
from mai.llm.lmstudio_provider import LMStudioProvider
from mai.llm.openai_compatible_provider import OpenAICompatibleProvider
from mai.llm.types import ChatProvider

logger = logging.getLogger(__name__)


def get_chat_provider() -> ChatProvider:
    """Return the active backend (default: LM Studio)."""
    if LLM_PROVIDER == "openai_compatible":
        return OpenAICompatibleProvider(
            api_url=LLM_API_URL,
            default_model=LLM_MODEL,
            api_key=LLM_API_KEY,
        )
    return LMStudioProvider(api_url=LLM_API_URL, default_model=LLM_MODEL)


def log_provider_on_startup() -> None:
    p = get_chat_provider()
    logger.info(
        "LLM provider: %s available=%s url=%s",
        p.kind,
        p.is_available(),
        LLM_API_URL[:80],
    )
