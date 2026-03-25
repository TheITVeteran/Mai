from __future__ import annotations

import json
import logging
from pathlib import Path

from mai.config import MEMORY_FILE, STATE_FILE
from mai.vault.types import MemoryData, StateData

logger = logging.getLogger(__name__)

_warned_memory_missing: set[Path] = set()
_warned_state_missing: set[Path] = set()


def load_memory() -> MemoryData:
    """Load memories from the vault memory.json file."""
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        key = Path(MEMORY_FILE)
        if key not in _warned_memory_missing:
            _warned_memory_missing.add(key)
            logger.warning(
                "Memory file not found, starting empty: %s", MEMORY_FILE
            )
        return {}
    except json.JSONDecodeError:
        logger.warning("Memory file is not valid JSON: %s", MEMORY_FILE)
        return {}
    except Exception:
        logger.exception("Error loading memories from %s", MEMORY_FILE)
        return {}


def load_state() -> StateData:
    """Load agent state from state.json."""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        key = Path(STATE_FILE)
        if key not in _warned_state_missing:
            _warned_state_missing.add(key)
            logger.warning(
                "State file not found, starting empty: %s", STATE_FILE
            )
        return {}
    except json.JSONDecodeError:
        logger.warning("State file is not valid JSON: %s", STATE_FILE)
        return {}
    except Exception:
        logger.exception("Error loading state from %s", STATE_FILE)
        return {}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Loading memories...")
    load_memory()
    logger.info("Loading state...")
    load_state()
