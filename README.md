# Mai - Discord AI Companion Bot

A Discord bot that feels like talking to a real person with genuine emotions, built with Discord.py and a pluggable local/remote LLM (LM Studio by default).

## Features

- 🤖 Powered by local LMStudio (privacy-first)
- 💕 Emotional, personality-driven responses
- 🎭 Real character depth (protective, playful, vulnerable)
- 🎮 Discord-native interaction
- 🚀 Built for iterative development

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

- **L3-8B-Stheno-v3.2** (GGUF IQ-Imatrix) — download GGUF files from [Hugging Face: `Lewdiculous/L3-8B-Stheno-v3.2-GGUF-IQ-Imatrix`](https://huggingface.co/Lewdiculous/L3-8B-Stheno-v3.2-GGUF-IQ-Imatrix), then load the `.gguf` you want in LM Studio.

## Layout

- `mai_bot.py` — run the bot (`python mai_bot.py` or `python -m mai.bot`)
- `mai/` — application package
  - `config.py` — paths, LLM + Discord, limits (env-overridable; `LLM_*` with `LMSTUDIO_*` legacy fallbacks)
  - `llm/` — provider-agnostic chat (`ChatParams`, `get_chat_provider()`; default `lmstudio`, optional `openai_compatible`)
  - `personality.py` — system prompts (`personal` vs `public`, switch with `MAI_PERSONA`)
  - `bot.py` — Discord client and message flow
  - `vault/` — `memory.json` / `state.json` I/O, normalisation, context string (`mai/vault/SCHEMA.md`)
  - `lmstudio.py` — LM Studio wire format (`post_chat` + `extract_assistant_text`), used by the LM Studio provider
- `scripts/test_lmstudio.py` — quick LM Studio POST smoke test
- `.env.example` — environment template (safe to commit)
- `.env` — secrets (gitignored)

## Next Steps

- [ ] Add conversation memory (short-term)
- [ ] Add JSON file persistence (long-term)
- [ ] Emotional state tracking
- [ ] Better prompt engineering
- [ ] Database integration (later)

## Lint

```bash
flake8 mai tests scripts mai_bot.py
```

Config: `.flake8` (100-char lines; `E402` allowed only where `load_dotenv()` must run before imports).

## License

MIT
