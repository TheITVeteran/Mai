"""Obsidian vault JSON memory (read / write / prompt context)."""

from mai.vault.context import build_context_string, get_recent_interaction
from mai.vault.reader import load_memory, load_state
from mai.vault.writer import (
    add_interaction,
    restore_from_backup,
    save_memory,
    save_state,
)

__all__ = [
    "add_interaction",
    "build_context_string",
    "get_recent_interaction",
    "load_memory",
    "load_state",
    "restore_from_backup",
    "save_memory",
    "save_state",
]
