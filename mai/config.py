from pathlib import Path
import os

import discord

# Vault layout (override with VAULT_PATH)
VAULT_PATH = Path(os.getenv("VAULT_PATH", "/mnt/d/Vaults/CafeCovenVault/Coven/Agents/Mai"))
MEMORY_FILE = VAULT_PATH / "memory.json"
STATE_FILE = VAULT_PATH / "state.json"
BACKUP_FILE = VAULT_PATH / "memory.backup.json"

MAX_INTERACTIONS = int(os.getenv("MAX_INTERACTIONS", "10"))
REQUEST_TIMEOUT_S = int(os.getenv("REQUEST_TIMEOUT_S", "120"))

LMSTUDIO_MODEL = os.getenv("LMSTUDIO_MODEL", "l3-8b-stheno-v3.2-iq-imatrix")
LMSTUDIO_API_URL = os.getenv(
    "LMSTUDIO_API_URL", "http://localhost:1234/api/v1/chat"
)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

DISCORD_INTENTS = discord.Intents.default()
DISCORD_INTENTS.message_content = True
DISCORD_CLIENT = discord.Client(intents=DISCORD_INTENTS)
