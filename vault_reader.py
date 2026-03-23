import json
from pathlib import Path
from config import VAULT_PATH

def load_memory():
    """Load memories from the vault file."""
    memory_file = VAULT_PATH / "memory.json"

    # Try to load the memory file
    try:
        with open(memory_file, "r", encoding="utf-8") as f:
            memory_data = json.load(f)
        return memory_data
    except Exception as e:
        print(f"Error loading memories: {e}")
        return {}

def load_state():
    """Load the state from the vault file."""
    state_file = VAULT_PATH / "state.json"

    # Try to load the state file
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state_data = json.load(f)
        return state_data
    except Exception as e:
        print(f"Error loading state: {e}")
        return {}

# Test the functions
if __name__ == "__main__":
    print("Loading memories...")
    memories = load_memory()
    print("Loading state...")
    state = load_state()