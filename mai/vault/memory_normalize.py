"""Normalize and lightly migrate in-memory vault dicts after JSON load."""

from __future__ import annotations

import logging

from mai.vault.types import MemoryData, StateData

logger = logging.getLogger(__name__)


def normalize_memory_data(data: MemoryData) -> MemoryData:
    """
    Ensure ``memory.json`` shape expected by writer/context.

    - ``short_term_memory``: dict with ``recent_interactions`` (list of dicts)
    - ``long_term_memory``: dict with ``facts_learned`` (list)
    Invalid or mistyped sections are replaced with empty structures; valid
    entries are preserved.
    """
    out: MemoryData = dict(data)

    stm_raw = out.get("short_term_memory")
    if not isinstance(stm_raw, dict):
        if stm_raw is not None:
            logger.warning("short_term_memory was not an object; replaced with {}")
        stm: dict = {}
    else:
        stm = dict(stm_raw)

    recent = stm.get("recent_interactions")
    if not isinstance(recent, list):
        if recent is not None:
            logger.warning("recent_interactions was not a list; replaced with []")
        recent_clean: list = []
    else:
        recent_clean = [x for x in recent if isinstance(x, dict)]

    stm["recent_interactions"] = recent_clean

    focus = stm.get("current_focus")
    if focus is not None and not isinstance(focus, str):
        stm["current_focus"] = str(focus)

    out["short_term_memory"] = stm

    ltm_raw = out.get("long_term_memory")
    if not isinstance(ltm_raw, dict):
        if ltm_raw is not None:
            logger.warning("long_term_memory was not an object; replaced with {}")
        ltm = {}
    else:
        ltm = dict(ltm_raw)

    facts = ltm.get("facts_learned")
    if not isinstance(facts, list):
        if facts is not None:
            logger.warning("facts_learned was not a list; replaced with []")
        facts = []
    ltm["facts_learned"] = facts

    out["long_term_memory"] = ltm

    return out


def normalize_state_data(data: StateData) -> StateData:
    """Ensure ``state.json`` has a dict ``emotional_state`` with list ``recent_changes``."""
    out: StateData = dict(data)

    es_raw = out.get("emotional_state")
    if not isinstance(es_raw, dict):
        if es_raw is not None:
            logger.warning("emotional_state was not an object; replaced with {}")
        es = {}
    else:
        es = dict(es_raw)

    rc = es.get("recent_changes")
    if not isinstance(rc, list):
        if rc is not None:
            logger.warning("recent_changes was not a list; replaced with []")
        es["recent_changes"] = []
    else:
        es["recent_changes"] = [x for x in rc if isinstance(x, dict)]

    out["emotional_state"] = es
    return out
