"""Tests for vault memory/state normalisation."""

from __future__ import annotations

from mai.vault.memory_normalize import normalize_memory_data, normalize_state_data


def test_normalize_memory_empty():
    out = normalize_memory_data({})
    assert out["short_term_memory"] == {"recent_interactions": []}
    assert out["long_term_memory"] == {"facts_learned": []}


def test_normalize_memory_repairs_interactions_and_facts():
    raw = {
        "short_term_memory": {
            "recent_interactions": [{"user_message": "a"}, 7, None],
        },
        "long_term_memory": {"facts_learned": "nope"},
    }
    out = normalize_memory_data(raw)
    assert len(out["short_term_memory"]["recent_interactions"]) == 1
    assert out["short_term_memory"]["recent_interactions"][0]["user_message"] == "a"
    assert out["long_term_memory"]["facts_learned"] == []


def test_normalize_memory_replaces_non_object_stm():
    raw = {
        "short_term_memory": "bad",
        "long_term_memory": {},
    }
    out = normalize_memory_data(raw)
    assert out["short_term_memory"] == {"recent_interactions": []}


def test_normalize_memory_coerces_focus():
    out = normalize_memory_data(
        {
            "short_term_memory": {
                "recent_interactions": [],
                "current_focus": 123,
            },
            "long_term_memory": {},
        }
    )
    assert out["short_term_memory"]["current_focus"] == "123"


def test_normalize_state_repairs_emotional_state():
    out = normalize_state_data({"emotional_state": "x"})
    assert out["emotional_state"] == {"recent_changes": []}


def test_normalize_state_filters_recent_changes():
    out = normalize_state_data(
        {
            "emotional_state": {
                "recent_changes": [{"a": 1}, "skip", None],
            }
        }
    )
    assert out["emotional_state"]["recent_changes"] == [{"a": 1}]
