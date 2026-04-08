# Mai Bot — TODO

## How to use this file

1. **Start in [Pick a task](#pick-a-task-recommended-order)** — each row tells you where to open the code and how you know you’re done.
2. When you finish something: change **`[ ]` → `[x]`** in [Open backlog](#open-backlog), add a file pointer if it helps the next person, or move stale completed bullets into [Shipped baseline](#shipped-baseline).
3. **Stack snapshot (2026-04):** Discord → **`mai/bot.py`** loads/saves **`memory.json`** / **`state.json`**. Context: **`mai/vault/context.py`** `build_context_string` (emotion, mood, `mai_felt_tone`, **`relationship_state`**, recent lines, **`facts_learned`**). Analysis: **`mai/vault/emotional_analyzer.py`** (LLM + NLP, `apply_analysis_to_state`, relationship caps/floors). Facts: **`mai/vault/fact_extractor.py`** + **`writer.add_facts`**. Chat: **`mai/llm/`** (`LLM_PROVIDER`, LM Studio or OpenAI-compatible). Settings: **`mai/config.py`**, **`.env.example`**.

---

## Pick a task (recommended order)

Work top-to-bottom if you care most about **continuity and “feels like a friend”**; skip around if you’re fixing ops or tests.

| # | Task | Start here | Done when |
|---|------|------------|-----------|
| 1 | **Restart / persistence check** | Your real `VAULT_PATH`; `memory.json` + `state.json` | **Automated:** `pytest tests/test_smoke_persistence.py -q` (simulated restart via temp vault). **Manual:** after killing and restarting the real bot, confirm the next reply’s behavior still matches persisted facts + relationship + emotion. |
| 2 | **LLM timeouts & offline path** | `mai/config.py` **`REQUEST_TIMEOUT_S`**, **`CHAT_OFFLINE_REPLY`**; `mai/bot.py` (chat `complete` try/except → offline reply, then usual memory/state/facts); `mai/vault/emotional_analyzer.py` `_lmstudio_analysis`; **`docs/SETUP.md`** “When the LLM is offline” | User still gets a reply and persistence when the **chat** LLM errors; analyzer already degrades deep LLM → NLP. **Tests:** `pytest tests/test_bot_offline_chat.py -q`. **Optional polish:** shorter default timeout, metrics, narrower `except` types. |
| 3 | **Single process guard** | `pgrep -af mai_bot` (or your entrypoint); `mai/config.py` `REPLY_SANITIZE` | You have a written note (here or `docs/README.md`): how duplicates happen, how to check, when to enable `REPLY_SANITIZE`. |
| 4 | **`should_update_state` tuning** | `mai/vault/emotional_analyzer.py` `should_update_state` (thresholds **0.45** LLM / **0.55** NLP today — **not** env-driven yet) | Either document the current numbers for operators **or** add env vars in `mai/config.py` + `.env.example` + tests in `tests/test_emotional_analyzer.py`. |
| 5 | **Analysis logging** | `mai/vault/emotional_analyzer.py`; `mai/logging_config.py` | Important analysis decisions (or failures) land in structured logs (level + fields), not only ad-hoc prints. |
| 6 | **Mood vs primary emotion rules** | `emotional_analyzer.py` `apply_analysis_to_state` (mood vs `primary_emotion` / confidence gating) | Written rule: when mood updates vs when only emotion does; tests or comments reflecting that rule. |
| 7 | **Fact memory: frequency / recency** | `mai/vault/writer.py` `add_facts`; `mai/vault/types` or schema; `context.py` | Facts carry e.g. `seen_count` / `last_seen` (or equivalent); context prefers “sticky” or repeated facts appropriately; migration in `memory_normalize.py` if needed. |
| 8 | **Tune fact extraction** | `mai/vault/fact_extractor.py`; prompts/heuristics | You’re happy with what gets stored; dedupe still sane at `MAX_FACTS_LEARNED`. |
| 9 | **Impact: numbers → voice** | `mai/personality.py`; prompt assembly in `mai/bot.py` (or wherever system/user prompts are built) | Trust/bond/mood/facts **measurably** change how she speaks (e.g. warmth, directness), not only the context block. |
|10 | **Integration tests** | `tests/` — add `tests/integration/` or extend existing | At least one test runs reader → context → writer path (temp dir) without Discord. |
|11 | **Personality drift (later)** | `state.json` schema; `emotional_analyzer` / dedicated module | Small cumulative trait shifts when trust is stable; optional `state.json` audit fields. |
|12 | **Multi-turn emotional hints (later)** | New small module or `memory.json` short-term structure | Context includes a short “recent pattern” line (e.g. recurring tone), not only last *N* messages. |

---

## Open backlog

### Reliability & ops

- [ ] Restart / persistence sanity (task **#1**)
- [x] LLM timeouts & chat offline fallback (task **#2** — main reply + docs + tests; optional: tighter `except`, telemetry)
- [ ] Single-bot process + when to use `REPLY_SANITIZE` (task **#3**)
- [ ] Structured analysis logging (task **#5**)

### Emotional / relationship logic

- [ ] `should_update_state`: document or env-configure (task **#4**)
- [ ] Mood vs primary emotion confidence / update rules (task **#6**)
- [ ] Personality drift + drift audit in state (task **#11**)

### Memory & facts

- [ ] Richer fact recency/frequency (`seen_count` / `last_seen` or equivalent) (task **#7**)
- [ ] Tune `fact_extractor` / dedupe for your voice (task **#8**)

### Presence & narrative (bigger lifts)

- [ ] Multi-turn emotional memory / pattern hints (task **#12**)
- [ ] Relationship milestones & inside jokes — **design doc first** (who triggers what, caps, anti-spam)
- [ ] “What do you think of me?” synthesis from facts + emotional history (after memory work is solid)

### Testing

- [ ] Broader integration / regression (task **#10**)

### Product / optional

- [ ] Slash commands for emotional / state queries (dev or user-facing — decide)
- [ ] Small dashboard for emotional state
- [ ] Voice I/O
- [ ] Public character deployment (Character.ai / etc.)
- [ ] Mobile companion
- [ ] Obsidian vault sync automation
- [ ] Open-source release checklist

### Multi-agent (only after single-agent loop feels solid)

- [ ] Additional companions (e.g. Rin, Yuki), inter-bot tone, shared vs per-agent vault

---

## Shipped baseline

Use this as the “what already exists” picture; don’t duplicate long checkbox history above.

- **Discord path:** message in → analysis → vault persist → reply with **`build_context_string`** context.
- **Relationship:** `relationship_state` in `state.json` (trust, bond, familiarity, `total_interactions`); `relationship_impact` from analyzer; caps/floors (`MAX_TRUST_SHIFT_PER_TURN`, harsh-message penalties, etc.).
- **Facts:** NLP + LLM extraction; `facts_learned` in `memory.json`; last few facts in context; `MAX_FACTS_LEARNED`.
- **LLM:** `mai/llm` providers; shared timeouts; `mai/lmstudio.post_chat` for LM Studio HTTP.
- **Quality:** logging (`mai/logging_config.py`); vault schema (`mai/vault/SCHEMA.md`, `docs/README.md`); normalize/migrate on load; `.flake8`; unit tests for vault, analyzer, LLM (mocked).
- **E2E:** Discord path verified (analysis → `state.json` → next turn context).

---

## Design tensions to revisit

These are **not** single tasks — they guide tuning:

1. **Emotional persistence** — Does `state.json` + prose change how she *feels* across sessions, not only metrics?
2. **Trust / bond** — Caps exist; adjust env vars until progression feels right.
3. **Facts** — Storage should match how you want to be known over time.
4. **Impact** — Same as pick-a-task **#9**: metrics must show up in **behavior**, not only in the hidden prompt.

---

## Changelog

| Date | Note |
|------|------|
| 2026-04-07 | Reorganized around “pick a task”; merged backlog; added shipped baseline; noted `should_update_state` is code constants today. |
| 2026-04-07 | Task **#1**: automated smoke test `tests/test_smoke_persistence.py` (simulated vault restart). |
| 2026-04-07 | Task **#2**: `CHAT_OFFLINE_REPLY` + chat `complete` fallback in `mai/bot.py`; docs in `docs/SETUP.md`; tests `tests/test_bot_offline_chat.py`. |
