import os
from dotenv import load_dotenv
import discord
import requests
from mai_personality import MAI_SYSTEM_PROMPT

# Load .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# LMStudio settings
API_URL = "http://localhost:1234/api/v1/chat"
MODEL_NAME = "l3-8b-stheno-v3.2-iq-imatrix"

# Setup the Discord Bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Conversation History (STM)
conversation_history = []

async def get_mai_response(user_message: str) -> str:
    """
    Send a message to LMStudio with Mai's personality and get her response.
    """
    # Combine the system prompt with the user message
    full_input = f"{MAI_SYSTEM_PROMPT}\n\nUser: {user_message}"
    payload = {
        "model": MODEL_NAME,
        "input": full_input
    }

    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()

        data = response.json()
        # Extract Reply
        mai_response = data['output'][0]['content']
        return mai_response
    except Exception as e:
        print(f"Error calling LMStuiod: {e}")
        return "Sorry, I had trouble thinking... try again?"

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    # Don't respond to our own messages
    if message.author == client.user:
        return

    print(f"{message.author}: {message.content}")

    # show typing
    async with message.channel.typing():
        # Get Mai's reply
        mai_response = await get_mai_response(message.content)

        # Send it back to Discord
        await message.channel.send(mai_response)

# Run the bot
client.run(DISCORD_TOKEN) 
