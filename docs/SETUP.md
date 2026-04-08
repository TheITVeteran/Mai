# Setup

## Requirements

- Python **3.10+**
- A [Discord bot](https://discord.com/developers/applications) token
- A running LLM endpoint (default: [LM Studio](https://lmstudio.ai/) local server) or any OpenAI-compatible chat API

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configure

1. Copy **`.env.example`** → **`.env`**
2. Set **`DISCORD_TOKEN`**
3. Set **`VAULT_PATH`** to a folder where `memory.json` and `state.json` should live (must exist or be creatable)
4. Point **`LLM_API_URL`** / **`LLM_MODEL`** at your model (or use the `LMSTUDIO_*` variables — see `.env.example`)
5. For OpenAI-style servers only: **`LLM_PROVIDER=openai_compatible`** and a full URL ending in `/v1/chat/completions`, plus **`LLM_API_KEY`** if required

## Portrait

For the image on the main **README**, save her picture as **`assets/Mai.png`** (create the `assets` folder if needed).

## Run

```bash
python mai_bot.py
```

Equivalent: **`python -m mai.bot`**

Start only **one** bot process per token (duplicate processes can double-reply).

## Model suggestion

**L3-8B-Stheno-v3.2** (GGUF):  
https://huggingface.co/Lewdiculous/L3-8B-Stheno-v3.2-GGUF-IQ-Imatrix  

Smoke-test LM Studio HTTP: **`scripts/test_lmstudio.py`**

## When the LLM is offline

- **`REQUEST_TIMEOUT_S`** caps how long each HTTP chat call waits (default **120** seconds). Lower it (e.g. **30**) if you want faster failures.
- If the **main chat** request errors (connection refused, timeout, HTTP error, bad JSON), Mai sends **`CHAT_OFFLINE_REPLY`** (configurable in `.env`) but still **appends the turn to memory**, runs **emotional analysis** (NLP / hybrid fallback—see `mai/vault/emotional_analyzer.py`), and runs **fact extraction** (NLP if the LLM path fails).
- **`EMOTION_ANALYSIS_MODE=llm`** still keeps fast NLP as a base for merges; deep analysis failures fall back to NLP-only (see `_lmstudio_analysis`).
- For a fully local NLP-only path during outages you can set **`EMOTION_ANALYSIS_MODE=fast`** so the analyzer never calls the emotion LLM (main Discord reply still needs the chat model unless it errors, then you get the offline reply).
