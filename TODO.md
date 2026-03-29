# Mai Bot — TODO

**Keeping it current:** When something ships, turn its checkbox **`[ ]` → `[x]`** and add a short pointer (file/module) if useful. Leave completed lines in place until a section feels crowded—then move that block to the bottom under a “Done” heading or trim it. Open work stays **`[ ]`**.

Brief notes on what already exists: emotional analysis runs after each reply in `mai/bot.py`, results are merged into `state.json` via `EmotionalAnalyzer.apply_analysis_to_state`, and `build_context_string` feeds emotion/mood/`mai_felt_tone`, **`relationship_state`** (trust / bond / familiarity), plus `facts_learned` into the prompt. Confidence gating is implemented in `should_update_state()`. **`relationship_impact`** deltas are applied to **`relationship_state`** (see `mai/vault/emotional_analyzer.py`). Not yet built: env **shift caps** per turn and **rule-based** trust drops on harsh messages (still relies on model/NLP suggestions only).

---

## Immediate (this week)

### Emotional system

- [X] End-to-end test on Discord: message → analysis → `state.json` → next turn sees updated context
- [ ] Harden / verify LM Studio timeouts and offline path in the analyzer (NLP fallback already exists)
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
- [ ] **Caps + rules:** env max shift per turn; optional trust/bond **decrease** heuristics on harsh/rude messages (today: whatever the LM/NLP puts in `relationship_impact`)
- [x] Surface relationship lightly in **`build_context_string`** (`mai/vault/context.py`) — prose + percentages when `relationship_state` exists

#### Auto-learn facts

- [ ] Detect declarative user facts (“I work in…”, “I have a cat…”)
- [ ] Store in **`memory.json`** under existing `long_term_memory.facts_learned` (avoid duplicating a second “semantic” store unless you migrate)
- [ ] Reference learned facts in responses (context already lists last few facts — validate quality)
- [ ] Track recency/frequency on facts if needed

#### Personality drift (after trust is stable)

- [ ] Small cumulative shifts from dominant emotional patterns
- [ ] Log notable drift in `state.json` (audit trail)

### Testing & validation

- [x] Unit tests (`tests/`, pytest): vault reader/writer/context + `emotional_analyzer` (NLP mocked, LM path mocked)
- [ ] Memory persistence: restart bot, recall recent interaction
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

- [x] Shared LM Studio HTTP helper (`mai/lmstudio.post_chat` — bot, emotional analyzer, `scripts/test_lmstudio.py`)
- [x] Consistent logging (`mai/logging_config.py`, `LOG_LEVEL`, vault + bot use `logging`)
- [x] Document vault schema (`mai/vault/SCHEMA.md` + README layout)
- [x] Validate / migrate on load (`mai/vault/memory_normalize.py` from `reader.load_memory` / `load_state`)

---

## High-priority unblocks

1. **Emotional persistence** — Does state carry across sessions in a way she actually uses?
2. **Trust / bond** — **`relationship_state`** in `state.json` updates from `relationship_impact`; tune caps/rules if it feels too fast/slow or never punishes rudeness
3. **Facts** — Are user facts extracted and recalled (`facts_learned`)?
4. **Impact** — Do trust/mood/facts change behavior measurably, not only the prompt block?

Use the convention at the top of this file when you close out tasks.
