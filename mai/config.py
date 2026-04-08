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
MAX_FACTS_LEARNED = max(5, min(500, _env_int("MAX_FACTS_LEARNED", 80)))

# ---------------------------------------------------------------------------
# LLM (provider-agnostic; primary default = LM Studio)
# ---------------------------------------------------------------------------

REQUEST_TIMEOUT_S = _env_int("REQUEST_TIMEOUT_S", 120)


def _env_non_empty_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    s = str(raw).strip()
    return s if s else default


# Used when the chat LLM raises (timeouts, connection refused, bad JSON, etc.).
CHAT_OFFLINE_REPLY = _env_non_empty_str(
    "CHAT_OFFLINE_REPLY",
    "I'm having trouble reaching the model right now—I'm still here. Try again in a moment?",
)

LMSTUDIO_MODEL = os.getenv(
    "LMSTUDIO_MODEL", "l3-8b-stheno-v3.2-iq-imatrix"
)
LMSTUDIO_API_URL = os.getenv(
    "LMSTUDIO_API_URL", "http://localhost:1234/api/v1/chat"
)

LMSTUDIO_USE_SYSTEM_PROMPT = _env_bool("LMSTUDIO_USE_SYSTEM_PROMPT", True)

LMSTUDIO_MAX_OUTPUT_TOKENS = max(
    50, min(4000, _env_int("LMSTUDIO_MAX_OUTPUT_TOKENS", 720))
)
LMSTUDIO_REPEAT_PENALTY = _env_float_clamped(
    "LMSTUDIO_REPEAT_PENALTY", 1.08, 1.0, 2.0
)


def _optional_env_float(name: str) -> float | None:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return None
    try:
        return float(raw)
    except ValueError:
        return None


LMSTUDIO_TEMPERATURE = _optional_env_float("LMSTUDIO_TEMPERATURE")

# Generic env names; fall back to LMSTUDIO_* so existing setups keep working.
LLM_PROVIDER: str = _env_choice(
    "LLM_PROVIDER",
    "lmstudio",
    frozenset({"lmstudio", "openai_compatible"}),
)
LLM_API_URL = (
    os.getenv("LLM_API_URL") or LMSTUDIO_API_URL or "http://localhost:1234/api/v1/chat"
).strip()
LLM_MODEL = (os.getenv("LLM_MODEL") or LMSTUDIO_MODEL).strip()
LLM_MAX_OUTPUT_TOKENS = max(
    50,
    min(
        4000,
        _env_int(
            "LLM_MAX_OUTPUT_TOKENS",
            int(LMSTUDIO_MAX_OUTPUT_TOKENS),
        ),
    ),
)
LLM_REPEAT_PENALTY = _env_float_clamped(
    "LLM_REPEAT_PENALTY",
    float(LMSTUDIO_REPEAT_PENALTY),
    1.0,
    2.0,
)
LLM_USE_SYSTEM_PROMPT = _env_bool(
    "LLM_USE_SYSTEM_PROMPT",
    LMSTUDIO_USE_SYSTEM_PROMPT,
)
_llm_temp = _optional_env_float("LLM_TEMPERATURE")
LLM_TEMPERATURE = _llm_temp if _llm_temp is not None else LMSTUDIO_TEMPERATURE

# Optional Bearer for OpenAI-compatible servers.
_raw_key = (os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
LLM_API_KEY = _raw_key or None

# Trim rare double-speech artifacts in one message (one bot process usually enough).
REPLY_SANITIZE = _env_bool("REPLY_SANITIZE", False)

# ---------------------------------------------------------------------------
# Persona
# ---------------------------------------------------------------------------

# System prompt variant in mai/personality.py: personal (default) vs public (forks).
MAI_PERSONA: str = _env_choice(
    "MAI_PERSONA",
    "personal",
    frozenset({"personal", "public"}),
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

# ===========================================================================
# Relationship state caps and rules
MAX_TRUST_SHIFT_PER_TURN = float(os.getenv("MAX_TRUST_SHIFT_PER_TURN", "0.15"))
MAX_BOND_SHIFT_PER_TURN = float(os.getenv("MAX_BOND_SHIFT_PER_TURN", "0.12"))
MAX_FAMILIARITY_SHIFT_PER_TURN = float(
    os.getenv("MAX_FAMILIARITY_SHIFT_PER_TURN", "0.10")
)
HARSH_MESSAGE_TRUST_PENALTY = float(
    os.getenv("HARSH_MESSAGE_TRUST_PENALTY", "-0.10")
)
HARSH_MESSAGE_BOND_PENALTY = float(
    os.getenv("HARSH_MESSAGE_BOND_PENALTY", "-0.08")
)
