"""Defaults for Discord-visible fallbacks stay in-character (no AI/bot framing)."""

from __future__ import annotations

import re

import mai.config as config

_BANNED_WORDS = (
    r"\bai\b",
    r"\bbot\b",
    r"\bllm\b",
    r"\bmodel\b",
    r"\bneural\b",
    r"\bsoftware\b",
    r"\bassistant\b",
    r"\bchatbot\b",
    r"\bcognitive\b",
    r"\balgorithm\b",
)


def _assert_no_banned_words(text: str, label: str) -> None:
    low = text.lower()
    for pat in _BANNED_WORDS:
        assert re.search(pat, low) is None, f"{label} must not match {pat!r}: {text!r}"


def test_chat_offline_and_failure_replies_avoid_fourth_wall_tech():
    _assert_no_banned_words(config.CHAT_OFFLINE_REPLY, "CHAT_OFFLINE_REPLY")
    _assert_no_banned_words(config.CHAT_FAILURE_REPLY, "CHAT_FAILURE_REPLY")
