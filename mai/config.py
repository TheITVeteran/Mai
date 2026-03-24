"""Load settings from the environment (see `.env.example`)."""

from __future__ import annotations

import os
from pathlib import Path

import discord

# ---------------------------------------------------------------------------
# Small parsers
# ---------------------------------------------------------------------------


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float_clamped(name: str, default: float, lo: float, hi: float) -> float:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return max(lo, min(hi, float(raw)))
    except ValueError:
        return default


def _env_choice(name: str, default: str, allowed: frozenset[str]) -> str:
    raw = (os.getenv(name) or default).strip().lower()
    return raw if raw in allowed else default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def _parse_snowflake_set(raw: str | None) -> frozenset[int]:
    """Comma- or whitespace-separated Discord IDs (channels, categories, etc.)."""
    if not raw or not str(raw).strip():
        return frozenset()
    ids: list[int] = []
    for token in raw.replace(",", " ").split():
        t = token.strip()
        if not t:
            continue
        try:
            ids.append(int(t))
        except ValueError:
            continue
    return frozenset(ids)


# ---------------------------------------------------------------------------
# Vault
# ---------------------------------------------------------------------------

VAULT_PATH = Path(
    os.getenv("VAULT_PATH", "/mnt/d/Vaults/CafeCovenVault/Coven/Agents/Mai")
)
MEMORY_FILE = VAULT_PATH / "memory.json"
STATE_FILE = VAULT_PATH / "state.json"
BACKUP_FILE = VAULT_PATH / "memory.backup.json"

MAX_INTERACTIONS = _env_int("MAX_INTERACTIONS", 10)

# ---------------------------------------------------------------------------
# LM Studio / HTTP
# ---------------------------------------------------------------------------

REQUEST_TIMEOUT_S = _env_int("REQUEST_TIMEOUT_S", 120)
LMSTUDIO_MODEL = os.getenv(
    "LMSTUDIO_MODEL", "l3-8b-stheno-v3.2-iq-imatrix"
)
LMSTUDIO_API_URL = os.getenv(
    "LMSTUDIO_API_URL", "http://localhost:1234/api/v1/chat"
)

# ---------------------------------------------------------------------------
# Discord
# ---------------------------------------------------------------------------

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# If non-empty, the bot only reads/replies in these guild channel IDs (snowflakes).
# Leave unset or empty to allow every guild channel the bot can see.
DISCORD_ALLOWED_CHANNEL_IDS: frozenset[int] = _parse_snowflake_set(
    os.getenv("DISCORD_ALLOWED_CHANNEL_IDS")
)

# Private / group DMs (message.guild is None). Independent of the channel allowlist.
DISCORD_ALLOW_DMS: bool = _env_bool("DISCORD_ALLOW_DMS", True)

DISCORD_INTENTS = discord.Intents.default()
DISCORD_INTENTS.message_content = True
DISCORD_CLIENT = discord.Client(intents=DISCORD_INTENTS)

# ---------------------------------------------------------------------------
# Emotion pipeline
# ---------------------------------------------------------------------------

EMOTION_ANALYSIS_MODE = _env_choice(
    "EMOTION_ANALYSIS_MODE",
    "hybrid",
    frozenset({"fast", "hybrid", "llm"}),
)
EMOTION_STATE_BLEND = _env_float_clamped("EMOTION_STATE_BLEND", 0.4, 0.0, 1.0)
