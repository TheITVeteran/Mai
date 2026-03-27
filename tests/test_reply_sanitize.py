"""Tests for reply sanitization helpers."""

from __future__ import annotations

from mai.reply_sanitize import sanitize_mai_reply, strip_stage_parentheticals


def test_strip_stage_parentheticals_whole_line():
    raw = (
        "Ooh exciting! Tell me more.\n\n"
        "(Playful and eager, leaning into their enthusiasm)"
    )
    out = strip_stage_parentheticals(raw)
    assert "Playful and eager" not in out
    assert "Tell me more" in out


def test_strip_stage_parentheticals_trailing_glued():
    raw = "I'm curious! (Playful and eager, leaning into their enthusiasm)"
    out = strip_stage_parentheticals(raw)
    assert out == "I'm curious!"


def test_strip_keeps_short_parens():
    assert strip_stage_parentheticals("Nice (lol)") == "Nice (lol)"


def test_sanitize_applies_paren_strip():
    raw = "Hello.\n\n(Narrator voice with many words here)"
    out = sanitize_mai_reply(raw, min_chars_before_cut=5)
    assert "Narrator voice" not in out
