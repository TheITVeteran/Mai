import os
import sys

import discord
import requests
from dotenv import load_dotenv

from mai_personality import MAI_SYSTEM_PROMPT
from vault_reader import load_memory, load_state
from vault_context_builder import build_context_string
from vault_writer import add_interaction, save_memory

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
API_URL = os.getenv("LMSTUDIO_API_URL", "http://localhost:1234/api/v1/chat")
MODEL_NAME = os.getenv("LMSTUDIO_MODEL", "l3-8b-stheno-v3.2-iq-imatrix")
REQUEST_TIMEOUT_S = 120

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


async def get_mai_response(user_message: str) -> str:
    """
    Send a message to LMStudio with Mai's personality and memory context
    then save the interaction to the vault.
    """
    try:
        #Load memory and state
        memory_data = load_memory()
        state_data = load_state()

        #Build context
        memory_context = build_context_string(memory_data, state_data)

        # Build the full prompt: system prompt + memory context + user message
        full_input = MAI_SYSTEM_PROMPT

        if memory_context:
            full_input += (
                f"\n\n-----MEMORY CONTEXT-----\n{memory_context}\n-----END MEMORY-----"
            )

        full_input += f"\n\nUser: {user_message}"

        payload = {
            "model": MODEL_NAME,
            "input": full_input,
        }

        response = requests.post(
            API_URL, json=payload, timeout=REQUEST_TIMEOUT_S
        )
        response.raise_for_status()

        data = response.json()
        mai_response = data["output"][0]["content"]

        # Save the interaction to the vault
        memory = add_interaction(memory_data, user_message, mai_response)
        save_memory(memory)

        return mai_response
    except Exception as e:
        print(f"Error getting Mai response: {e}")
        return "Sorry, I had trouble thinking... try again?"

@client.event
async def on_ready():
    print(f"{client.user} has connected to Discord!")
    
    # Test Vault I/O
    try:
        memory = load_memory()
        interactions = memory.get("short_term_memory", {}).get("recent_interactions", [])
        print(f"Vault loaded! Mai has {len(interactions)} memories")
    except Exception as e:
        print(f"Couldn't load vault: {e}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    print(f"{message.author}: {message.content}")

    async with message.channel.typing():
        mai_response = await get_mai_response(message.content)
        await message.channel.send(mai_response)


def main():
    if not DISCORD_TOKEN:
        print("Missing DISCORD_TOKEN. Copy .env.example to .env and set your token.")
        sys.exit(1)
    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
