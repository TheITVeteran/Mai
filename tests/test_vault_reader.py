"""Tests for mai.vault.reader."""

from __future__ import annotations

import json

from mai.vault.reader import load_memory, load_state


def test_load_memory_missing_returns_empty(isolated_vault):
    assert load_memory() == {}


def test_load_memory_valid_json(isolated_vault):
    p = isolated_vault["memory"]
    p.write_text(json.dumps({"short_term_memory": {"recent_interactions": []}}), encoding="utf-8")
    data = load_memory()
    assert data["short_term_memory"]["recent_interactions"] == []


def test_load_memory_invalid_json_returns_empty(isolated_vault):
    isolated_vault["memory"].write_text("{not json", encoding="utf-8")
    assert load_memory() == {}


def test_load_memory_non_object_root_returns_empty(isolated_vault):
    isolated_vault["memory"].write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    assert load_memory() == {}


def test_load_state_missing_returns_empty(isolated_vault):
    assert load_state() == {}


def test_load_state_valid(isolated_vault):
    isolated_vault["state"].write_text(
        json.dumps({"emotional_state": {"primary_emotion": "calm"}}),
        encoding="utf-8",
    )
    assert load_state()["emotional_state"]["primary_emotion"] == "calm"


def test_load_state_non_object_root_returns_empty(isolated_vault):
    isolated_vault["state"].write_text('"scalar"', encoding="utf-8")
    assert load_state() == {}
