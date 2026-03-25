"""Tests for mai.vault.writer."""

from __future__ import annotations

import json

from mai.vault.reader import load_memory
from mai.vault.writer import (
    add_interaction,
    restore_from_backup,
    save_memory,
    save_state,
)


def test_add_interaction_creates_structure(isolated_vault):
    m = add_interaction({}, "hi", "hello")
    stm = m["short_term_memory"]
    assert len(stm["recent_interactions"]) == 1
    turn = stm["recent_interactions"][0]
    assert turn["user_message"] == "hi"
    assert turn["mai_response"] == "hello"
    assert "timestamp" in turn
    assert m.get("last_updated")


def test_add_interaction_repairs_bad_stm(isolated_vault):
    m = {"short_term_memory": "broken"}
    m2 = add_interaction(m, "a", "b")
    assert isinstance(m2["short_term_memory"], dict)
    assert len(m2["short_term_memory"]["recent_interactions"]) == 1


def test_add_interaction_trims_to_max(monkeypatch, isolated_vault):
    monkeypatch.setattr("mai.vault.writer.MAX_INTERACTIONS", 2)
    m: dict = {}
    for i in range(4):
        m = add_interaction(m, f"u{i}", f"m{i}")
    recent = m["short_term_memory"]["recent_interactions"]
    assert len(recent) == 2
    assert recent[-1]["user_message"] == "u3"


def test_save_memory_writes_roundtrip(isolated_vault):
    m = add_interaction({}, "ping", "pong")
    assert save_memory(m) is True
    loaded = load_memory()
    assert loaded["short_term_memory"]["recent_interactions"][-1]["user_message"] == "ping"


def test_save_memory_creates_backup_when_file_exists(isolated_vault):
    path = isolated_vault["memory"]
    backup = isolated_vault["backup"]
    path.write_text(json.dumps({"v": 1}), encoding="utf-8")
    save_memory(add_interaction({}, "a", "b"))
    assert backup.is_file()
    old = json.loads(backup.read_text(encoding="utf-8"))
    assert old == {"v": 1}


def test_save_state_atomic(isolated_vault):
    st = {"emotional_state": {"primary_emotion": "hopeful"}}
    assert save_state(st) is True
    raw = isolated_vault["state"].read_text(encoding="utf-8")
    assert json.loads(raw)["emotional_state"]["primary_emotion"] == "hopeful"


def test_restore_from_backup(isolated_vault):
    mem = isolated_vault["memory"]
    bak = isolated_vault["backup"]
    mem.write_text(json.dumps({"lost": True}), encoding="utf-8")
    bak.write_text(json.dumps({"restored": True}), encoding="utf-8")
    assert restore_from_backup() is True
    assert json.loads(mem.read_text(encoding="utf-8")) == {"restored": True}


def test_restore_from_backup_missing(isolated_vault):
    assert restore_from_backup() is False
