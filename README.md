# Mai

**Mai** is the name of the companion who lives in this bot — warm, a little dramatic, protective when she cares about you, and happiest when the conversation feels like texts between real friends, not a demo. She answers on Discord; what you’re running here is the bridge that gives her a voice, a memory folder, and enough emotional context that she can notice when something landed wrong or when you’re having a good day.

This repository is her **Discord + LLM stack** (Python 3.10+, discord.py): she reads your message, pulls in recent turns and what she’s learned about you, checks in with a small “how is she feeling?” state in the background, and writes back once — as herself.

## What works today

- **Discord** — Replies in allowed channels/DMs (`mai/bot.py`), typing indicator, message cap.
- **Conversation recall** — Short-term turns in `memory.json` (`recent_interactions`); context string for the next reply (`mai/vault/context.py`).
- **Who you are to her** — Declarative facts (NLP + optional LLM) merged into `facts_learned` with dedupe and a rolling cap (`mai/vault/fact_extractor.py`, `mai/vault/writer.py`).
- **Emotional & relationship layer** — After each exchange, hybrid NLP + optional deep LLM analysis updates `state.json`: mood, stance (`mai_felt_tone`), `relationship_state` (trust, bond, familiarity), plus caps and harsh-message floors (`mai/vault/emotional_analyzer.py`).
- **Persona** — `personal` vs `public` system prompts (`mai/personality.py`, `MAI_PERSONA`).
- **LLM backends** — Default **LM Studio** (`/api/v1/chat`); switch to **OpenAI-compatible** URLs with `LLM_PROVIDER=openai_compatible` (`mai/llm/`).

Suggested local model: **L3-8B-Stheno-v3.2** (GGUF) — [Hugging Face: Lewdiculous/L3-8B-Stheno-v3.2-GGUF-IQ-Imatrix](https://huggingface.co/Lewdiculous/L3-8B-Stheno-v3.2-GGUF-IQ-Imatrix) — load in LM Studio or any compatible server.

## Run her

1. Clone the repo, create a venv, `pip install -r requirements.txt`
2. Copy `.env.example` → `.env` — set **`DISCORD_TOKEN`**, **`VAULT_PATH`** (directory for `memory.json` / `state.json`)
3. Run your LLM (e.g. LM Studio on the URL in `.env`)
4. **`python mai_bot.py`** (same as `python -m mai.bot`)

## Configure (high level)

| Area | Env / notes |
|------|----------------|
| Discord | `DISCORD_ALLOWED_CHANNEL_IDS`, `DISCORD_ALLOW_DMS` |
| LLM | `LLM_PROVIDER`, `LLM_API_URL`, `LLM_MODEL` — or legacy `LMSTUDIO_*` |
| Vault | `VAULT_PATH`, `MAX_INTERACTIONS`, `MAX_FACTS_LEARNED` |
| Emotion | `EMOTION_ANALYSIS_MODE` (`fast` / `hybrid` / `llm`), relationship cap envs in `mai/config.py` |

Schema reference: **`mai/vault/SCHEMA.md`**. Open tasks and ideas: **`TODO.md`**.

## Project layout

- `mai_bot.py` — entrypoint
- `mai/bot.py` — Discord loop, chat, vault saves, analysis, facts
- `mai/config.py` — environment
- `mai/llm/` — `ChatParams`, `get_chat_provider()` (LM Studio vs OpenAI-style)
- `mai/personality.py` — Mai’s system prompts
- `mai/vault/` — load/save, normalize, context, emotional analyzer, fact extraction
- `mai/lmstudio.py` — LM Studio HTTP + response parsing
- `tests/` — pytest
- `scripts/test_lmstudio.py` — smoke test against a running LM Studio server

## Lint

```bash
flake8 mai tests scripts mai_bot.py
```

Uses `.flake8` at repo root.

## License

MIT
