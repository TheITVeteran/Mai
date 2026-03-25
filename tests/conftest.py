"""Shared fixtures for vault tests."""

from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import pytest


@pytest.fixture
def isolated_vault(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Point reader/writer at temp files (no real Obsidian path)."""
    memory = tmp_path / "memory.json"
    state = tmp_path / "state.json"
    backup = tmp_path / "memory.backup.json"
    monkeypatch.setattr("mai.vault.reader.MEMORY_FILE", memory)
    monkeypatch.setattr("mai.vault.reader.STATE_FILE", state)
    monkeypatch.setattr("mai.vault.writer.MEMORY_FILE", memory)
    monkeypatch.setattr("mai.vault.writer.BACKUP_FILE", backup)
    monkeypatch.setattr("mai.vault.writer.STATE_FILE", state)
    return {"memory": memory, "state": state, "backup": backup}
