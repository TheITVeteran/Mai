# Mai - Discord AI Companion Bot

A Discord bot that feels like talking to a real person with genuine emotions, built with LMStudio and Discord.py.

## Features

- Powered by local LM Studio (privacy-first)
- Personality-driven responses with emotional depth
- Discord-native interaction
- Small codebase, easy to extend

## Current Status (MVP)

- [x] Discord bot responds naturally in chat
- [x] LMStudio integration
- [x] Personality system
- [x] Emotional responses
- [ ] Conversation history/memory
- [ ] Long-term memory
- [ ] Advanced features (moods, relationships, etc.)

## Setup

1. Clone the repo
2. Create virtual environment: `python3 -m venv .venv`
3. Activate: `source .venv/bin/activate`
4. Install: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and set `DISCORD_TOKEN`
6. Start LMStudio locally
7. Run: `python mai_bot.py`

## Tech Stack

- **LMStudio** - Local LLM inference (privacy & control)
- **Discord.py** - Discord bot framework
- **Python 3.10+** - Core language

## Model

- L3-8B-Stheno-v3.2 (GGUF IQ-Imatrix)

## Files

- `mai_bot.py` - Main bot logic
- `mai_personality.py` - Mai's personality/system prompt
- `test_lmstudio.py` - LM Studio connection test
- `.env.example` - Environment variable template (safe to commit)
- `.env` - Your secrets (gitignored; never commit)

## Next Steps

- [ ] Add conversation memory (short-term)
- [ ] Add JSON file persistence (long-term)
- [ ] Emotional state tracking
- [ ] Better prompt engineering
- [ ] Database integration (later)

## License

MIT
