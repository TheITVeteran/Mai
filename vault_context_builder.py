def get_recent_interaction(memory_data: dict, count: int = 5) -> list:
    """
    Get the last N interactions from the memory data.

    Args:
        memory_data: The memory data.
        count: The number of interactions to get.
    Returns:
        A list of interactions.
    """
    interactions = memory_data.get("short_term_memory", {}).get("recent_interactions", [])
    return interactions[-count:] if interactions else []

def build_context_string(memory_data: dict, state_data: dict) -> str:
    """
    Build the context for the LLM.

    Args:
        memory_data: The memory data.
        state_data: The state data.
    Returns:
        A string of the context.
    """
    context_parts = []

    # 1. Add current emotional state
    emotion = state_data.get("emotional_state", {}).get("primary_emotion", "neutral")
    mood = state_data.get("emotional_state", {}).get("mood", "")
    context_parts.append(f"Current emotional state: {emotion}")
    if mood:
        context_parts.append(f"Mood: {mood}")

    # 2. Add recent interactions
    recent = get_recent_interaction(memory_data, count=3)
    if recent:
        context_parts.append("\nRecent conversations:")
        for interaction in recent:
            user_msg = interaction.get("user_message", "")[:80]
            context_parts.append(f"- {user_msg}")

    # 3. Add learned facts
    facts = memory_data.get("long_term_memory", {}).get("facts_learned", [])
    if facts:
        context_parts.append("\nFacts I Know")
        for fact in facts[-3:]:
            fact_text = fact.get("fact", "") if isinstance(fact, dict) else fact
            context_parts.append(f"- {fact_text}")
    
    # 4. Add current focus
    focus = memory_data.get("short_term_memory", {}).get("current_focus", "")
    if focus:
        context_parts.append(f"\nCurrent Focus: {focus}")
    
    return "\n".join(context_parts)

# Test the functions
if __name__ == "__main__":
    from vault_reader import load_memory, load_state

    print("Loading memory and state...")
    memory_data = load_memory()
    state_data = load_state()

    print("\n" + "="*60)
    print("CONTEXT BUILDER TEST")
    print("="*60)
    context = build_context_string(memory_data, state_data)
    print(context)
    print("="*60)