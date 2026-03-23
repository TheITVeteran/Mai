import json
from pathlib import Path
from datetime import datetime

# Define the path to the vault file
VAULT_PATH = Path("/mnt/d/Vaults/CafeCovenVault/Coven/Agents/Mai")
MEMORY_FILE = VAULT_PATH / "memory.json"

def load_memory():
    """Load the memory.json file. (so we can modify it)"""
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading memory.json: {e}")
        return {}

def add_interaction(memory_data: dict, user_message: str, mai_response: str) -> dict:
    """
    Add a new interaction to the memory.

    Args:
        memory_data: The current memory data.
        user_message: The user's message.
        mai_response: The AI's response.
    Returns:
        The updated memory data.
    """
    # Create a new interaction
    interaction = {
        "timestamp": datetime.now().isoformat(),
        "user_message": user_message,
        "mai_response": mai_response,
        "user": "user",
    }

    # Ensure structure exists (short_term_memory must be a dict, not a list)
    stm = memory_data.get("short_term_memory")
    if not isinstance(stm, dict):
        memory_data["short_term_memory"] = {}
        stm = memory_data["short_term_memory"]
    stm.setdefault("recent_interactions", [])

    # Add the new interaction
    stm["recent_interactions"].append(interaction)

    # Keep only the latest 10 interactions
    if len(stm["recent_interactions"]) > 10:
        stm["recent_interactions"] = stm["recent_interactions"][-10:]
    
    memory_data["last_updated"] = datetime.now().isoformat()

    return memory_data

def save_memory(memory_data: dict) -> bool:
    """
    Save the memory back to the vault file.

    Args:
        memory_data: The memory data to save.
    Returns:
        True if successful, False otherwise.
    """
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory_data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving memory.json: {e}")
        return False


# Test the functions
if __name__ == "__main__":
    print("Loading memory from vault...")
    memory_data = load_memory()
    print(f"Loaded {len(memory_data.get('short_term_memory', {}).get('recent_interactions', []))} interactions.")

    print("\nAdding a test interaction...")
    test_user = "Hi Mai! How's the cafe today?"
    test_mai = "It's bustling! So many happy customers!"

    memory = add_interaction(memory_data, test_user, test_mai)
    print(f"User: {test_user}")
    print(f"Mai: {test_mai}")

    print("\nSaving memory to vault...")
    if save_memory(memory):
        print("Memory saved successfully.")

        # Verify by reloading
        print("\nVerifying reload...")
        memory_check = load_memory()
        interactions = memory_check.get("short_term_memory", {}).get("recent_interactions", [])
        print(f"Now have {len(interactions)} total interactions.")
        print(f"Latest interaction: {interactions[-1]}")
    else:
        print("Failed to save memory.")