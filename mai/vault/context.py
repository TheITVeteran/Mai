from __future__ import annotations

import logging
from typing import cast

from mai.vault.types import MemoryData, StateData, TurnRecord

logger = logging.getLogger(__name__)


def get_recent_interaction(
    memory_data: MemoryData, count: int = 5
) -> list[TurnRecord]:
    """Return the last N interactions from memory data."""
    raw = memory_data.get("short_term_memory", {}).get("recent_interactions", [])
    if not isinstance(raw, list) or not raw:
        return []
    interactions = [x for x in raw if isinstance(x, dict)]
    return cast(list[TurnRecord], interactions[-count:])


def build_context_string(memory_data: MemoryData, state_data: StateData) -> str:
    """Build a compact text block for the LLM from memory + state."""
    context_parts = []

    es = state_data.get("emotional_state") or {}
    if not isinstance(es, dict):
        es = {}
    emotion = es.get("primary_emotion", "neutral")
    mood = es.get("mood", "")
    felt = es.get("mai_felt_tone", "")
    context_parts.append(f"Current emotional state: {emotion}")
    if mood:
        context_parts.append(f"Mood: {mood}")
    if felt:
        context_parts.append(f"Mai's felt stance toward them: {felt}")

    recent = get_recent_interaction(memory_data, count=3)
    if recent:
        context_parts.append("\nRecent things they've said (for context):")
        for interaction in recent:
            user_msg = interaction.get("user_message", "")[:80]
            context_parts.append(f"- {user_msg}")

    facts = memory_data.get("long_term_memory", {}).get("facts_learned", [])
    if facts:
        context_parts.append("\nFacts I Know")
        for fact in facts[-3:]:
            fact_text = fact.get("fact", "") if isinstance(fact, dict) else fact
            context_parts.append(f"- {fact_text}")

    focus = memory_data.get("short_term_memory", {}).get("current_focus", "")
    if focus:
        context_parts.append(f"\nCurrent Focus: {focus}")

    return "\n".join(context_parts)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from mai.vault.reader import load_memory, load_state

    memory_data = load_memory()
    state_data = load_state()
    logger.info("Context preview:\n%s", build_context_string(memory_data, state_data))
