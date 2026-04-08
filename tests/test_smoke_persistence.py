"""Smoke test for docs/TODO.md task #1 — vault survives a simulated process restart.

The bot reads ``memory.json`` and ``state.json`` from disk on startup. This test writes
realistic data through ``save_memory`` / ``save_state``, then reloads with ``load_*``
as a new process would, and checks facts, relationship, emotion, and ``build_context_string``.
"""

from __future__ import annotations

from mai.vault.context import build_context_string
from mai.vault.reader import load_memory, load_state
from mai.vault.writer import add_facts, add_interaction, save_memory, save_state


def test_vault_persistence_survives_simulated_restart(isolated_vault):
    """Disk → save → reload from disk → context still reflects memory + state."""
    mem: dict = {}
    mem = add_interaction(mem, "User says hi", "Mai waves back.")
    mem = add_facts(mem, ["User's favorite drink is oat milk."])
    assert save_memory(mem) is True

    state = {
        "emotional_state": {
            "primary_emotion": "warm",
            "mood": "Quietly glad they showed up.",
            "mai_felt_tone": "Soft and attentive.",
            "confidence": 0.8,
        },
        "relationship_state": {
            "trust_level": 0.72,
            "bond_strength": 0.65,
            "familiarity": 0.58,
            "total_interactions": 42,
        },
    }
    assert save_state(state) is True

    mem2 = load_memory()
    state2 = load_state()

    recent = mem2["short_term_memory"]["recent_interactions"]
    assert recent[-1]["user_message"] == "User says hi"
    assert recent[-1]["mai_response"] == "Mai waves back."

    facts = mem2["long_term_memory"]["facts_learned"]
    assert any(
        isinstance(f, dict) and "oat milk" in str(f.get("fact", "")).lower()
        for f in facts
    )

    es = state2["emotional_state"]
    assert es["primary_emotion"] == "warm"
    assert "glad" in str(es.get("mood", "")).lower()

    rel = state2["relationship_state"]
    assert isinstance(rel, dict)
    assert abs(float(rel["trust_level"]) - 0.72) < 0.001
    assert int(rel["total_interactions"]) == 42

    ctx = build_context_string(mem2, state2)
    assert "oat milk" in ctx.lower()
    assert "warm" in ctx.lower()
    assert "72%" in ctx
    assert "Relationship with them" in ctx
