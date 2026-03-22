import json
from pathlib import Path

# Define the path to the vault file
VAULT_PATH = Path("/mnt/d/Vaults/CafeCovenVault/Coven/Agents/Mai")

def load_memories():
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

def get_recent_interactions(memory_data: dict, count: int = 5) -> list:
    """Get the last N interactions from memory.

    Args:
        memory_data: The memory data to search through
        count: The number of interactions to return

    Returns:
        A list of the last N interactions
    """
    interactions = memory_data.get("short_term_memory", {}).get("recent_interactions", [])
    return interactions[-count:] if interactions else []

def build_context_summary(memory_data: dict, state_data: dict) -> str:
    """Build a summary of the context from memory and state.

    Args:
        memory_data: The memory data to search through
        state_data: The state data to search through

    Returns:
        A summary of the context
    """
    context_parts = []

    # 1. Add current emotional state
    emotion = state_data.get("emotional_state", {}).get("current_emotion", "neutral")
    mood = state_data.get("mood", {}).get("mood", "")
    context_parts.append(f" Current emotion: {emotion}")
    if mood:
        context_parts.append(f" Mood: {mood}")
    
    # 2. Add recent interactions (for continuity)
    recent = get_recent_interactions(memory_data, count=3)
    if recent:
        context_parts.append("\nRecent conversations:")
        for interaction in recent:
            user_msg = interaction.get("user_message", "")[:80]
            context_parts.append(f" {user_msg}")
    
    # 3. Add learned facts
    facts = memory_data.get("long_term_memory", {}).get("facts_learned", [])
    if facts:
        context_parts.append("\nFacts I know:")
        for fact in facts[-3:]:
            fact_text = fact.get("fact", "") if isinstance(fact, dict) else fact
            context_parts.append(f" - {fact_text}")
    
    # 4. Add current focus
    focus = memory_data.get("short_term_memory", {}).get("current_focus", "")
    if focus:
        context_parts.append(f"\nCurrent focus: {focus}")
    
    return "\n".join(context_parts)

# Test the functions
if __name__ == "__main__":
    print("Loading memories...")
    memories = load_memories()
    print("Loading state...")
    state = load_state()
    
    # Build context
    print("\n" + "="*60)
    print("CONTEXT TO INJECT INTO LMSTUDIO:")
    print("="*60)
    context = build_context_summary(memories, state)
    print(context)
    print("="*60)
