# Vault JSON schemas

Paths come from **`VAULT_PATH`** (see `mai/config.py`): default `memory.json` and `state.json` in that folder.

On load, **`mai/vault/reader.py`** parses JSON and runs **`memory_normalize.normalize_memory_data`** / **`normalize_state_data`** so missing or wrong-typed sections are repaired without crashing the bot.

## `memory.json`

Top-level object. Main sections:

| Key | Type | Purpose |
|-----|------|--------|
| `short_term_memory` | object | Rolling conversation buffer |
| `short_term_memory.recent_interactions` | array of objects | Each turn: `timestamp`, `user_message`, `mai_response`, optional `user` |
| `short_term_memory.current_focus` | string (optional) | Short topic hint for context |
| `long_term_memory` | object | Durable extracted knowledge |
| `long_term_memory.facts_learned` | array | Items are `{ "fact": "..." }` objects or legacy strings |
| `last_updated` | string (optional) | ISO timestamp; set when saving |

**Normalisation:** If `short_term_memory` or `long_term_memory` is not an object, it is replaced with `{}`. `recent_interactions` / `facts_learned` lists are rebuilt: non-dict interaction rows are dropped; non-list `facts_learned` becomes `[]`.

## `state.json`

Top-level object. Main sections:

| Key | Type | Purpose |
|-----|------|--------|
| `emotional_state` | object | Current affect snapshot |
| `emotional_state.primary_emotion` | string | e.g. `neutral`, `happy` |
| `emotional_state.secondary_emotions` | array of strings (optional) | |
| `emotional_state.valence` / `arousal` / `dominance` / `intensity` | number (optional) | Scalars in expected ranges after analysis |
| `emotional_state.mood` | string (optional) | Short mood line |
| `emotional_state.mai_felt_tone` | string (optional) | Mai’s stance toward the user |
| `emotional_state.confidence` | number (optional) | Last analysis confidence |
| `emotional_state.recent_changes` | array of objects | Audit tail from `EmotionalAnalyzer.apply_analysis_to_state` |
| `timestamp` | string (optional) | ISO time of last state write |

**Normalisation:** If `emotional_state` is not an object, it is replaced with `{}`. `recent_changes` is filtered to dict-only entries.

## Code map

- **Load + normalise:** `mai/vault/reader.py`
- **Normalise helpers:** `mai/vault/memory_normalize.py`
- **Write:** `mai/vault/writer.py`
- **Prompt block:** `mai/vault/context.build_context_string`
