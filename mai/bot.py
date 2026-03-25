import asyncio
import logging
import sys
from copy import deepcopy

import requests
from dotenv import load_dotenv

load_dotenv()

from mai.config import (
    DISCORD_ALLOWED_CHANNEL_IDS,
    DISCORD_ALLOW_DMS,
    DISCORD_CLIENT as client,
    DISCORD_TOKEN,
    LMSTUDIO_API_URL,
    LMSTUDIO_MAX_OUTPUT_TOKENS,
    LMSTUDIO_MODEL,
    LMSTUDIO_REPEAT_PENALTY,
    LMSTUDIO_TEMPERATURE,
    LMSTUDIO_USE_SYSTEM_PROMPT,
    REPLY_SANITIZE,
    REQUEST_TIMEOUT_S,
)
from mai.lmstudio import extract_assistant_text
from mai.personality import MAI_SYSTEM_PROMPT
from mai.reply_sanitize import sanitize_mai_reply
from mai.vault import (
    add_interaction,
    build_context_string,
    load_memory,
    load_state,
    save_memory,
    save_state,
)
from mai.vault.emotional_analyzer import EmotionalAnalyzer
from mai.logging_config import configure_logging

logger = logging.getLogger(__name__)

_emotion_analyzer = EmotionalAnalyzer()

_DISCORD_MESSAGE_CAP = 2000

_TURN_SUFFIX = (
    "\n\n(They just messaged you on Discord — answer them as Mai, fully yourself. "
    "Stay one message / one send, but gesture, warmth, and little stage bits are fine "
    "if they feel natural.)\n\n"
    "User: {user}\nMai:"
)


def _trim_discord(text: str, limit: int = _DISCORD_MESSAGE_CAP) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _channel_allowed(message) -> bool:
    if message.guild is None:
        return DISCORD_ALLOW_DMS
    if not DISCORD_ALLOWED_CHANNEL_IDS:
        return True
    return message.channel.id in DISCORD_ALLOWED_CHANNEL_IDS


async def get_mai_response(user_message: str) -> str:
    """Run LM Studio + vault I/O in a thread so the Discord loop stays responsive."""

    def _sync_work():
        memory = load_memory()
        state = load_state()
        memory_context = build_context_string(memory, state)

        memory_block = ""
        if memory_context:
            memory_block = (
                "\n\n--- MEMORY CONTEXT ---\n"
                "(Continuity and emotional background — your reply is to what they say "
                'under "User:" at the end.)\n'
                f"{memory_context}\n"
                "--- END MEMORY ---"
            )
        turn = _TURN_SUFFIX.format(user=user_message)

        payload: dict = {
            "model": LMSTUDIO_MODEL,
            "max_output_tokens": LMSTUDIO_MAX_OUTPUT_TOKENS,
            "repeat_penalty": LMSTUDIO_REPEAT_PENALTY,
        }
        if LMSTUDIO_TEMPERATURE is not None:
            payload["temperature"] = LMSTUDIO_TEMPERATURE

        if LMSTUDIO_USE_SYSTEM_PROMPT:
            payload["system_prompt"] = MAI_SYSTEM_PROMPT.strip()
            payload["input"] = (memory_block + turn).lstrip()
        else:
            payload["input"] = (MAI_SYSTEM_PROMPT.strip() + memory_block + turn).lstrip()

        response = requests.post(
            LMSTUDIO_API_URL, json=payload, timeout=REQUEST_TIMEOUT_S
        )
        response.raise_for_status()

        data = response.json()
        mai_response = extract_assistant_text(data)
        if mai_response.lower().startswith("mai:"):
            mai_response = mai_response[4:].lstrip()
        if REPLY_SANITIZE:
            mai_response = sanitize_mai_reply(mai_response)
        mai_response = _trim_discord(mai_response)

        memory = add_interaction(memory, user_message, mai_response)
        if not save_memory(memory):
            logger.error("Failed to save memory.json")

        try:
            interactions = memory.get("short_term_memory", {}).get(
                "recent_interactions", []
            )
            history = interactions[:-1] if len(interactions) > 1 else []
            analysis = _emotion_analyzer.analyze_interaction(
                user_message,
                mai_response,
                conversation_history=history,
                current_state=state,
            )
            if analysis:
                new_state = _emotion_analyzer.apply_analysis_to_state(
                    deepcopy(state), analysis
                )
                if not save_state(new_state):
                    logger.error("Failed to save state.json")
        except Exception:
            logger.exception("Emotional state update skipped")

        return mai_response

    try:
        return await asyncio.to_thread(_sync_work)
    except Exception:
        logger.exception("get_mai_response failed")
        return "Sorry, I had trouble thinking... try again?"


@client.event
async def on_ready():
    logger.info("%s has connected to Discord", client.user)
    logger.info("DMs: %s", "allowed" if DISCORD_ALLOW_DMS else "ignored")
    if DISCORD_ALLOWED_CHANNEL_IDS:
        n = len(DISCORD_ALLOWED_CHANNEL_IDS)
        logger.info("Guild channel restriction: %s allowed ID(s)", n)
    else:
        logger.info(
            "Guild channel restriction: none (all guild channels the bot can access)"
        )
    try:
        memory = load_memory()
        interactions = memory.get("short_term_memory", {}).get(
            "recent_interactions", []
        )
        logger.info("Vault loaded: %s interaction(s) in short-term memory", len(interactions))
    except Exception:
        logger.exception("Could not load vault for startup summary")


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if not _channel_allowed(message):
        return

    logger.info("Message from %s: %s", message.author, message.content)

    async with message.channel.typing():
        mai_response = await get_mai_response(message.content)
        await message.channel.send(mai_response)


def main():
    configure_logging()
    if not DISCORD_TOKEN:
        logger.error(
            "Missing DISCORD_TOKEN. Copy .env.example to .env and set your token."
        )
        sys.exit(1)
    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
