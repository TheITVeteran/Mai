import os
import sys

import discord
import requests
from dotenv import load_dotenv

from mai_personality import MAI_SYSTEM_PROMPT

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
API_URL = os.getenv("LMSTUDIO_API_URL", "http://localhost:1234/api/v1/chat")
MODEL_NAME = os.getenv("LMSTUDIO_MODEL", "l3-8b-stheno-v3.2-iq-imatrix")
REQUEST_TIMEOUT_S = 120

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


async def get_mai_response(user_message: str) -> str:
    """Send a message to LM Studio with Mai's personality and return her reply."""
    full_input = f"{MAI_SYSTEM_PROMPT}\n\nUser: {user_message}"
    payload = {"model": MODEL_NAME, "input": full_input}

    try:
        response = requests.post(
            API_URL, json=payload, timeout=REQUEST_TIMEOUT_S
        )
        response.raise_for_status()
        data = response.json()
        return data["output"][0]["content"]
    except Exception as e:
        print(f"Error calling LM Studio: {e}")
        return "Sorry, I had trouble thinking... try again?"


@client.event
async def on_ready():
    print(f"{client.user} has connected to Discord!")


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
