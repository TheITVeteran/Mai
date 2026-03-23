import os
import sys
import asyncio

import discord
import requests
from dotenv import load_dotenv

from mai_personality import MAI_SYSTEM_PROMPT
from vault_reader import load_memory, load_state
from vault_context_builder import build_context_string
from vault_writer import add_interaction, save_memory

load_dotenv()

from config import (
    DISCORD_CLIENT as client,
    DISCORD_TOKEN,
    LMSTUDIO_API_URL,
    LMSTUDIO_MODEL,
    REQUEST_TIMEOUT_S,
)

# Function to get Mai's response
async def get_mai_response(user_message: str) -> str:
    """Async wrapper for LM Studio calls."""
    def _sync_work():
        # Load, build, save - all sync work here
        memory = load_memory()
        state = load_state()
        memory_context = build_context_string(memory, state)
        
        full_input = f"{MAI_SYSTEM_PROMPT}"
        if memory_context:
            full_input += f"\n\n--- MEMORY CONTEXT ---\n{memory_context}\n--- END MEMORY ---"
        full_input += f"\n\nUser: {user_message}"
        
        payload = {"model": LMSTUDIO_MODEL, "input": full_input}
        response = requests.post(
            LMSTUDIO_API_URL, json=payload, timeout=REQUEST_TIMEOUT_S
        )
        response.raise_for_status()
        
        data = response.json()
        mai_response = data['output'][0]['content']
        
        memory = add_interaction(memory, user_message, mai_response)
        if not save_memory(memory):
            print("⚠️  Save failed!")
        
        return mai_response
    
    try:
        # Run sync work in a thread pool - doesn't block Discord
        return await asyncio.to_thread(_sync_work)
    except Exception as e:
        print(f"Error: {e}")
        return "Sorry, I had trouble thinking... try again?"

# Event handler for when the bot is ready
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


# Event handler for when a message is sent
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    print(f"{message.author}: {message.content}")

    async with message.channel.typing():
        mai_response = await get_mai_response(message.content)
        await message.channel.send(mai_response)


# Main function to run the bot
def main():
    if not DISCORD_TOKEN:
        print("Missing DISCORD_TOKEN. Copy .env.example to .env and set your token.")
        sys.exit(1)
    client.run(DISCORD_TOKEN)


# Entry point
if __name__ == "__main__":
    main()
