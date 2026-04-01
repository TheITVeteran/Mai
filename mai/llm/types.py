"""Shared types for chat completion providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable


@dataclass(frozen=True)
class ChatParams:
    """One chat request, mapped to LM Studio or OpenAI-style APIs."""

    model: str
    user_prompt: str
    system_prompt: Optional[str] = None
    use_system_prompt_field: bool = True
    max_output_tokens: int = 720
    temperature: Optional[float] = None
    repeat_penalty: Optional[float] = None


@runtime_checkable
class ChatProvider(Protocol):
    """LLM backend: local LM Studio, OpenAI-compatible HTTP, etc."""

    @property
    def kind(self) -> str:
        """Short label for logging (e.g. ``lmstudio``, ``openai_compatible``)."""

        ...

    def is_available(self) -> bool:
        """Whether the provider is configured (e.g. non-empty base/URL)."""

        ...

    def complete(self, params: ChatParams, *, timeout: float) -> str:
        """Complete once; return assistant text (may raise on HTTP/parse errors)."""

        ...
