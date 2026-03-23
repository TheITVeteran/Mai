from pathlib import Path
import os
import discord

# Use ENV variables for config if available, otherwise use defaults

# VAULT PATH
VAULT_PATH = Path(os.getenv("VAULT_PATH", "/mnt/d/Vaults/CafeCovenVault/Coven/Agents/Mai"))

# MEMORY FILE
MEMORY_FILE = VAULT_PATH / "memory.json"

# STATE FILE
STATE_FILE = VAULT_PATH / "state.json"

# BACKUP FILE
BACKUP_FILE = VAULT_PATH / "memory.backup.json"

# MAX INTERACTIONS TO KEEP IN MEMORY
MAX_INTERACTIONS = int(os.getenv("MAX_INTERACTIONS", "10"))

# REQUEST TIMEOUT IN SECONDS
REQUEST_TIMEOUT_S = int(os.getenv("REQUEST_TIMEOUT_S", "120"))

# LM STUDIO MODEL NAME
LMSTUDIO_MODEL = os.getenv("LMSTUDIO_MODEL", "l3-8b-stheno-v3.2-iq-imatrix")

# LM STUDIO API URL
LMSTUDIO_API_URL = os.getenv("LMSTUDIO_API_URL", "http://localhost:1234/api/v1/chat")

# DISCORD TOKEN
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# DISCORD CLIENT INTENTS
DISCORD_INTENTS = discord.Intents.default()
DISCORD_INTENTS.message_content = True

# DISCORD CLIENT
DISCORD_CLIENT = discord.Client(intents=DISCORD_INTENTS)