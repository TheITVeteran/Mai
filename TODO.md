# Mai Bot — TODO

Brief notes on what already exists: emotional analysis runs after each reply in `mai/bot.py`, results are merged into `state.json` via `EmotionalAnalyzer.apply_analysis_to_state`, and `build_context_string` feeds emotion/mood/`mai_felt_tone` plus `facts_learned` into the prompt. Confidence gating is implemented in `should_update_state()`. `relationship_impact` from the analyzer is **not** yet persisted as a trust/bond scalar — that remains to build.

---

## Immediate (this week)

### Emotional system

- [ ] End-to-end test on Discord: message → analysis → `state.json` → next turn sees updated context
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

- [ ] Add persistent **`trust_level`** (or bond score) in `state.json` (e.g. start 0.5, clamp 0–1)
- [ ] Apply analyzer **`relationship_impact`** (trust/familiarity/bond shifts) in `apply_analysis_to_state` or adjacent helper
- [ ] Increase trust on vulnerability / warmth; decrease on harsh messages (rules + caps per turn)
- [ ] Surface trust lightly in context so replies can reflect it without scripted lines

#### Auto-learn facts

- [ ] Detect declarative user facts (“I work in…”, “I have a cat…”)
- [ ] Store in **`memory.json`** under existing `long_term_memory.facts_learned` (avoid duplicating a second “semantic” store unless you migrate)
- [ ] Reference learned facts in responses (context already lists last few facts — validate quality)
- [ ] Track recency/frequency on facts if needed

#### Personality drift (after trust is stable)

- [ ] Small cumulative shifts from dominant emotional patterns
- [ ] Log notable drift in `state.json` (audit trail)

### Testing & validation

- [ ] Test suite for `emotional_analyzer` (10+ cases: NLP path, LM path, merge, low confidence, empty input)
- [ ] Memory persistence: restart bot, recall recent interaction
- [ ] `state.json` + `recent_changes` with real Discord traffic
- [ ] Regression: vault reader/writer and context string shape

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

- [ ] Type hints across `mai/vault/*`
- [ ] Unit tests for `reader` / `writer` / context builder
- [ ] Shared LM Studio HTTP helper used by bot + analyzer
- [ ] Consistent logging module (replace stray prints where it matters)
- [ ] Document vault schema (`memory.json` / `state.json`) in README or `mai/vault/`
- [ ] Validate / migrate `memory.json` structure on load

---

## High-priority unblocks

1. **Emotional persistence** — Does state carry across sessions in a way she actually uses?
2. **Trust / bond** — Is there a number in `state.json` that moves and matters?
3. **Facts** — Are user facts extracted and recalled (`facts_learned`)?
4. **Impact** — Do trust/mood/facts change behavior measurably, not only the prompt block?

Update this file as items ship; archive completed sections rather than deleting history if you want a paper trail.
