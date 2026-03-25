"""Tests for mai.vault.context."""

from __future__ import annotations

from mai.vault.context import build_context_string, get_recent_interaction


def test_get_recent_empty():
    assert get_recent_interaction({}, 5) == []


def test_get_recent_not_a_list():
    m = {"short_term_memory": {"recent_interactions": "bad"}}
    assert get_recent_interaction(m, 5) == []


def test_get_recent_filters_non_dicts():
    m = {
        "short_term_memory": {
            "recent_interactions": [
                {"user_message": "keep"},
                "skip",
                {"user_message": "also"},
            ]
        }
    }
    out = get_recent_interaction(m, 10)
    assert len(out) == 2
    assert out[0]["user_message"] == "keep"


def test_get_recent_respects_count():
    m = {
        "short_term_memory": {
            "recent_interactions": [
                {"user_message": f"m{i}"} for i in range(5)
            ]
        }
    }
    recent = get_recent_interaction(m, 2)
    assert [x["user_message"] for x in recent] == ["m3", "m4"]


def test_build_context_emotion_and_mood():
    memory: dict = {}
    state = {
        "emotional_state": {
            "primary_emotion": "warm",
            "mood": "soft evening",
            "mai_felt_tone": "protective",
        }
    }
    s = build_context_string(memory, state)
    assert "Current emotional state: warm" in s
    assert "Mood: soft evening" in s
    assert "Mai's felt stance toward them: protective" in s


def test_build_context_skips_empty_mood_fields():
    memory: dict = {}
    state = {"emotional_state": {"primary_emotion": "neutral"}}
    s = build_context_string(memory, state)
    assert "Mood:" not in s
    assert "felt stance" not in s


def test_build_context_malformed_emotional_state():
    memory: dict = {}
    state = {"emotional_state": "broken"}
    s = build_context_string(memory, state)
    assert "Current emotional state: neutral" in s


def test_build_context_recent_and_facts_and_focus():
    memory = {
        "short_term_memory": {
            "recent_interactions": [
                {"user_message": "I had a long day"},
            ],
            "current_focus": "work stress",
        },
        "long_term_memory": {
            "facts_learned": [
                {"fact": "User has a cat"},
                "plain string fact",
            ]
        },
    }
    state = {"emotional_state": {}}
    s = build_context_string(memory, state)
    assert "Recent things they've said" in s
    assert "long day" in s
    assert "Facts I Know" in s
    assert "User has a cat" in s
    assert "plain string fact" in s
    assert "Current Focus: work stress" in s
