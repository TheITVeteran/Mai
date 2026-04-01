# Mai Bot — TODO

**Keeping it current:** When something ships, turn its checkbox **`[ ]` → `[x]`** and add a short pointer (file/module) if useful. Leave completed lines in place until a section feels crowded—then move that block to the bottom under a “Done” heading or trim it. Open work stays **`[ ]`**.

**Snapshot (Mar 2026):** Discord reply path loads/saves **`memory.json`** and **`state.json`**. `build_context_string` feeds emotion, mood, `mai_felt_tone`, **`relationship_state`**, and **`facts_learned`**. `EmotionalAnalyzer.apply_analysis_to_state` applies **`relationship_impact`** with env caps and harsh-message floors. Facts: **`extract_facts`** (NLP + LLM) + **`add_facts`** after each user message. Chat completions go through **`mai/llm`** (default LM Studio, optional OpenAI-compatible API).

---

## Immediate (this week)

### Emotional system

- [x] End-to-end test on Discord: message → analysis → `state.json` → next turn sees updated context
- [ ] Harden / verify LLM timeouts and offline path in the analyzer (NLP fallback already exists)
- [ ] Optional: structured logging of recent analyses (file or logger), not only prints on failure
- [ ] Review whether mood vs. primary emotion updates should use different confidence rules

### Integration & polish

- [ ] Tune or env-configure `should_update_state` thresholds if needed
- [ ] Confirm single-bot process when testing (`pgrep -af mai_bot` — duplicate processes double-reply)

---

## This month

### Core features

#### Relationship progression

- [x] Persistent **`relationship_state`** in `state.json`: `trust_level`, `bond_strength`, `familiarity`, `total_interactions` — defaults 0.5 / 0.5 / 0.5, clamped 0–1 (`mai/vault/emotional_analyzer.py` `apply_analysis_to_state`)
- [x] Apply analyzer **`relationship_impact`** shifts into that block (same place)
- [x] **Caps + rules:** env max shift per turn; harsh-message trust/bond floors (`_detect_harsh_message`, `_apply_relationship_caps_and_rules`)
- [x] Surface relationship lightly in **`build_context_string`** (`mai/vault/context.py`) — prose + percentages when `relationship_state` exists

#### Auto-learn facts

- [x] Detect declarative user facts — **`mai/vault/fact_extractor.py`** (**NLP** heuristics + **LLM** when provider available)
- [x] Store in **`memory.json`** → `long_term_memory.facts_learned` — **`mai/vault/writer.py`** `add_facts` (dedupe, trim with **`MAX_FACTS_LEARNED`**); wired in **`mai/bot.py`**
- [x] Reference learned facts in responses — **`build_context_string`** shows last few facts
- [ ] Richer recency/frequency (e.g. `seen_count` / `last_seen` reinforcement) if you want stronger “she remembers how often you said X”

#### Personality drift (after trust is stable)

- [ ] Small cumulative shifts from dominant emotional patterns
- [ ] Log notable drift in `state.json` (audit trail)

### Testing & validation

- [x] Unit tests (`tests/`, pytest): vault reader/writer/context + `emotional_analyzer` + LLM providers (mocked)
- [ ] Memory persistence: restart bot, sanity-check recall (file-backed; validate on your vault path)
- [x] `state.json` + `recent_changes` (+ `relationship_state`) exercised on real Discord traffic
- [ ] Broader integration / regression beyond unit scope

---

## Q2 (April+)

### Advanced

- [ ] Multi-turn emotional memory and simple pattern hints (e.g. recurring tones)
- [ ] Relationship milestones (first vulnerability, trust threshold, inside jokes) — design before code
- [ ] “What do you think of me?” style synthesis from facts + emotional history

### Multi-agent (only after single-agent loop feels solid)

- [ ] Additional companions (e.g. Rin, Yuki), inter-bot tone, shared vs. per-agent vault

---

## Optional / future

- [ ] Slash commands for emotional / state queries
- [ ] Small dashboard for emotional state
- [ ] Voice I/O
- [ ] Public character deployment (Character.ai / etc.)
- [ ] Mobile companion
- [ ] Obsidian vault sync automation
- [ ] Open-source release checklist

---

## Technical debt

- [x] Shared LM Studio HTTP helper (`mai/lmstudio.post_chat` — used by LM Studio provider)
- [x] Provider-agnostic chat layer (`mai/llm/`, `LLM_PROVIDER` / `openai_compatible`)
- [x] Consistent logging (`mai/logging_config.py`, `LOG_LEVEL`, vault + bot use `logging`)
- [x] Document vault schema (`mai/vault/SCHEMA.md` + README)
- [x] Validate / migrate on load (`mai/vault/memory_normalize.py` from `reader.load_memory` / `load_state`)
- [x] Flake8 config (`.flake8`)

---

## High-priority unblocks

1. **Emotional persistence** — Tune whether `state.json` + context prose changes how she *feels* across sessions (not only metrics).
2. **Trust / bond** — Caps/floors exist; dial env vars if it feels too fast/slow.
3. **Facts** — Pipeline is live; tune **`fact_extractor`** / prompts / dedupe so what she stores matches how you want to be known.
4. **Impact** — Do trust/mood/facts change behavior measurably, not only the prompt block?

Use the convention at the top of this file when you close out tasks.
