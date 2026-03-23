import json

from mai.config import MEMORY_FILE, STATE_FILE


def load_memory():
    """Load memories from the vault memory.json file."""
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading memories: {e}")
        return {}


def load_state():
    """Load agent state from state.json."""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading state: {e}")
        return {}


if __name__ == "__main__":
    print("Loading memories...")
    load_memory()
    print("Loading state...")
    load_state()
