from __future__ import annotations

import json

from mai.config import MEMORY_FILE, STATE_FILE
from mai.vault.types import MemoryData, StateData


def load_memory() -> MemoryData:
    """Load memories from the vault memory.json file."""
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"Error loading memories: {e}")
        return {}


def load_state() -> StateData:
    """Load agent state from state.json."""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"Error loading state: {e}")
        return {}


if __name__ == "__main__":
    print("Loading memories...")
    load_memory()
    print("Loading state...")
    load_state()
