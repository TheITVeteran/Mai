from __future__ import annotations

import json
import shutil
from datetime import datetime

from mai.config import BACKUP_FILE, MAX_INTERACTIONS, MEMORY_FILE, STATE_FILE
from mai.vault.types import MemoryData, StateData


def add_interaction(
    memory_data: MemoryData, user_message: str, mai_response: str
) -> MemoryData:
    """Append one turn to short-term memory and return updated dict."""
    interaction = {
        "timestamp": datetime.now().isoformat(),
        "user_message": user_message,
        "mai_response": mai_response,
        "user": "user",
    }

    stm = memory_data.get("short_term_memory")
    if not isinstance(stm, dict):
        memory_data["short_term_memory"] = {}
        stm = memory_data["short_term_memory"]
    stm.setdefault("recent_interactions", [])

    stm["recent_interactions"].append(interaction)

    if len(stm["recent_interactions"]) > MAX_INTERACTIONS:
        stm["recent_interactions"] = stm["recent_interactions"][-MAX_INTERACTIONS:]

    memory_data["last_updated"] = datetime.now().isoformat()
    return memory_data


def save_memory(memory: MemoryData) -> bool:
    """Atomically write memory.json; keep a backup when replacing an existing file."""
    backup_file = BACKUP_FILE
    try:
        if MEMORY_FILE.exists():
            shutil.copy2(MEMORY_FILE, backup_file)
            print(f"Backup created: {backup_file.name}")

        temp_file = MEMORY_FILE.with_suffix(".tmp.json")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)

        with open(temp_file, "r", encoding="utf-8") as f:
            json.load(f)

        temp_file.replace(MEMORY_FILE)

        saved_count = len(
            memory.get("short_term_memory", {}).get("recent_interactions", [])
        )
        print(f"Memory saved successfully. {saved_count} interactions saved.")
        return True
    except Exception as e:
        print(f"Error saving memory: {e}")
        print(f"Backup file: {backup_file.name}")
        return False


def save_state(state: StateData) -> bool:
    """Atomically write state.json (same pattern as memory)."""
    state_backup = STATE_FILE.with_suffix(".backup.json")
    try:
        if STATE_FILE.exists():
            shutil.copy2(STATE_FILE, state_backup)

        temp_file = STATE_FILE.with_suffix(".tmp.json")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        with open(temp_file, "r", encoding="utf-8") as f:
            json.load(f)

        temp_file.replace(STATE_FILE)
        return True
    except Exception as e:
        print(f"Error saving state.json: {e}")
        return False


def restore_from_backup() -> bool:
    """Restore memory.json from the backup copy."""
    if BACKUP_FILE.exists():
        shutil.copy2(BACKUP_FILE, MEMORY_FILE)
        print(f"Restored from backup: {BACKUP_FILE.name}")
        return True
    print("No backup file found to restore from.")
    return False


if __name__ == "__main__":
    from mai.vault.reader import load_memory

    memory_data = load_memory()
    n = len(memory_data.get("short_term_memory", {}).get("recent_interactions", []))
    print(f"Loaded {n} interactions.")

    memory = add_interaction(
        memory_data,
        "Hi Mai! How's the cafe today?",
        "It's bustling! So many happy customers!",
    )
    if save_memory(memory):
        check = load_memory()
        interactions = check.get("short_term_memory", {}).get("recent_interactions", [])
        print(f"Now have {len(interactions)} total interactions.")
