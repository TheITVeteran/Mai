"""Chat LLM failures still return a reply and persist the turn (docs/TODO.md #2)."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

import requests

from mai.vault.writer import add_interaction as vault_add_interaction


@pytest.fixture
def patch_bot_pipeline(monkeypatch: pytest.MonkeyPatch):
    """Avoid real vault files and Discord; isolate chat.complete failure path."""
    import mai.bot as bot_mod

    monkeypatch.setattr(bot_mod, "load_memory", lambda: {})
    monkeypatch.setattr(bot_mod, "load_state", lambda: {})

    captured: dict[str, str] = {}

    def _track_add(m, user, mai_reply):
        captured["stored_reply"] = mai_reply
        return vault_add_interaction(m, user, mai_reply)

    monkeypatch.setattr(bot_mod, "add_interaction", _track_add)
    monkeypatch.setattr(bot_mod, "save_memory", lambda _m: True)
    monkeypatch.setattr(bot_mod, "save_state", lambda _s: True)
    monkeypatch.setattr(bot_mod, "build_context_string", lambda _mem, _st: "")

    mock_chat = MagicMock()
    mock_chat.complete.side_effect = requests.ConnectionError("connection refused")
    monkeypatch.setattr(bot_mod, "get_chat_provider", lambda: mock_chat)

    offline = "[test-offline-reply]"
    monkeypatch.setattr(bot_mod, "CHAT_OFFLINE_REPLY", offline)

    return {"bot": bot_mod, "mock_chat": mock_chat, "captured": captured, "offline": offline}


def test_chat_llm_failure_uses_offline_reply_and_stores_turn(patch_bot_pipeline):
    """Short user message avoids hybrid emotion LLM; main chat still fails → fallback."""
    bot_mod = patch_bot_pipeline["bot"]
    captured = patch_bot_pipeline["captured"]
    offline = patch_bot_pipeline["offline"]
    mock_chat = patch_bot_pipeline["mock_chat"]

    out = asyncio.run(bot_mod.get_mai_response("hi"))

    assert out == offline
    assert captured["stored_reply"] == offline
    assert mock_chat.complete.call_count == 1


def test_chat_llm_failure_skips_truncated_empty_model_output(patch_bot_pipeline):
    """Malformed LLM path is still an exception from provider; same fallback."""
    bot_mod = patch_bot_pipeline["bot"]
    mock_chat = patch_bot_pipeline["mock_chat"]
    mock_chat.complete.side_effect = ValueError("LM Studio output contained no assistant message content")

    out = asyncio.run(bot_mod.get_mai_response("hi"))
    assert out == patch_bot_pipeline["offline"]
