"""Shared type aliases for vault JSON shapes (memory.json, state.json, analyzer output)."""

from __future__ import annotations

from typing import Any, TypeAlias

# Values inside memory/state are arbitrary JSON-serializable data.
MemoryData: TypeAlias = dict[str, Any]
StateData: TypeAlias = dict[str, Any]

# One element of short_term_memory.recent_interactions.
TurnRecord: TypeAlias = dict[str, Any]

# Output of EmotionalAnalyzer.analyze_interaction and related helpers.
EmotionAnalysis: TypeAlias = dict[str, Any]
