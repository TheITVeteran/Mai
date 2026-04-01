# Developers

## Layout

| Path | Role |
|------|------|
| `mai_bot.py` | CLI entry (`python mai_bot.py`) |
| `mai/bot.py` | Discord client, chat loop, vault saves, emotion + facts |
| `mai/config.py` | Environment-driven settings |
| `mai/llm/` | Chat providers (`lmstudio`, `openai_compatible`) |
| `mai/lmstudio.py` | LM Studio HTTP client + response parsing |
| `mai/personality.py` | System prompts (`MAI_PERSONA`) |
| `mai/vault/` | Memory/state I/O, context string, emotional analyzer, fact extractor |
| `mai/vault/SCHEMA.md` | `memory.json` / `state.json` field reference |
| `tests/` | `pytest` |
| `.flake8` | Lint rules |
| `docs/` | Setup, this file, TODO |

## Tests

```bash
pytest tests/
```

## Lint

```bash
flake8 mai tests scripts mai_bot.py
```

## License

See **`LICENSE`** (MIT).
