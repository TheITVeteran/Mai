"""Heuristic extraction of durable user facts into ``facts_learned``."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Iterator

from mai.config import FACT_LEARN_ENABLED, MAX_FACTS_LEARNED
from mai.vault.types import MemoryData

logger = logging.getLogger(__name__)

_MAX_CLAUSE_LEN = 220
_MIN_MESSAGE_LEN = 12

# Third-person phrasing for Mai's memory context (user is "they").
_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"^i(?:'m| am)\s+from\s+(.+)$", re.I),
        r"They're from \1",
    ),
    (
        re.compile(r"^i(?:'m| am)\s+called\s+(.+)$", re.I),
        r"They're called \1",
    ),
    (
        re.compile(r"^i(?:'m| am)\s+(.+)$", re.I),
        r"They're \1",
    ),
    (re.compile(r"^i work\s+(.+)$", re.I), r"They work \1"),
    (re.compile(r"^i live in\s+(.+)$", re.I), r"They live in \1"),
    (re.compile(r"^i grew up in\s+(.+)$", re.I), r"They grew up in \1"),
    (re.compile(r"^i study\s+(.+)$", re.I), r"They study \1"),
    (re.compile(r"^i went to\s+(.+)$", re.I), r"They went to \1"),
    (
        re.compile(r"^i was born in\s+(.+)$", re.I),
        r"They were born in \1",
    ),
    (re.compile(r"^my name is\s+(.+)$", re.I), r"Their name is \1"),
    (re.compile(r"^call me\s+(.+)$", re.I), r"They asked to be called \1"),
    (re.compile(r"^i prefer\s+(.+)$", re.I), r"They prefer \1"),
    (re.compile(r"^i like\s+(.+)$", re.I), r"They like \1"),
    (
        re.compile(r"^i(?: do not| don't) like\s+(.+)$", re.I),
        r"They don't like \1",
    ),
    (
        re.compile(r"^my favorite\s+(\w+)\s+is\s+(.+)$", re.I),
        r"Their favorite \1 is \2",
    ),
    (
        re.compile(r"^my favorite\s+is\s+(.+)$", re.I),
        r"Their favorite is \1",
    ),
    (
        re.compile(
            r"^i have\s+(?!to\s)(a|an|the|some|two|three|2|3)\s+(.+)$",
            re.I,
        ),
        r"They have \1 \2",
    ),
    (
        re.compile(r"^i have\s+(?!to\s)(?!no\s)(.+)$", re.I),
        r"They have \1",
    ),
]

# Drop "I have …" clauses that are idioms / non-facts.
_I_HAVE_SKIP = re.compile(
    r"^(?:to\s|no\s(?:idea|clue)|a\s(?:question|minute|second|moment|thought|feeling)|"
    r"been\s|got\s|to\sgo|n't\s)",
    re.I,
)

_SKIP_PREFIX = re.compile(r"^(?:\[test\]|[!/])", re.I)

_TEMP_STATE = re.compile(
    r"^i(?:'m| am)\s+feeling\b|^i(?:'m| am)\s+(?:a\s+little\s+|kinda\s+|sorta\s+)?"
    r"(?:tired|sick|ok|okay|fine|stressed|anxious|sad|happy|mad|angry|busy|done)\b",
    re.I,
)


def _clean_clause(text: str) -> str:
    s = text.strip().rstrip(".,!?:;")
    if len(s) > _MAX_CLAUSE_LEN:
        s = s[: _MAX_CLAUSE_LEN].rsplit(" ", 1)[0] + "…"
    return s


def _normalize_fact_key(text: str) -> str:
    s = re.sub(r"\s+", " ", text.lower().strip())
    s = s.strip(".,;:!?")
    return s


def _chunks_from_message(message: str) -> Iterator[str]:
    m = message.strip()
    if not m:
        return
    parts = re.split(r"(?i)\s+and\s+i\s+", m)
    for i, piece in enumerate(parts):
        chunk = piece if i == 0 else "I " + piece.strip()
        c = chunk.strip()
        if c:
            yield c


def extract_declarative_facts(user_message: str) -> list[str]:
    """Return zero or more third-person fact lines suitable for ``facts_learned``."""
    raw = user_message.strip()
    if not raw or len(raw) < _MIN_MESSAGE_LEN:
        return []
    if "?" in raw and raw.count("?") >= raw.count(".") + 1:
        # Mostly questions — skip auto-learn on this message.
        return []
    if _SKIP_PREFIX.search(raw):
        return []

    out: list[str] = []
    seen_keys: set[str] = set()

    for chunk in _chunks_from_message(raw):
        ch = chunk.strip()
        if len(ch) < 8:
            continue
        if _TEMP_STATE.match(ch):
            continue
        for pattern, template in _RULES:
            m = pattern.match(ch)
            if not m:
                continue
            try:
                rendered = m.expand(template)
            except (IndexError, re.error):
                continue
            rendered = _clean_clause(rendered)
            if not rendered or len(rendered) < 8:
                break
            # "They have" path: skip idioms
            if rendered.lower().startswith("they have "):
                rest = rendered[10:].strip()
                if _I_HAVE_SKIP.match(rest):
                    break
            key = _normalize_fact_key(rendered)
            if key and key not in seen_keys:
                seen_keys.add(key)
                out.append(rendered)
            break

    return out


def _fact_text(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("fact", "")).strip()
    return str(item).strip() if item else ""


def merge_learned_facts_from_user_message(
    memory_data: MemoryData, user_message: str
) -> MemoryData:
    """Append or reinforce facts from ``user_message`` into long-term memory."""
    if not FACT_LEARN_ENABLED:
        return memory_data

    candidates = extract_declarative_facts(user_message)
    if not candidates:
        return memory_data

    ltm = memory_data.get("long_term_memory")
    if not isinstance(ltm, dict):
        memory_data["long_term_memory"] = {}
        ltm = memory_data["long_term_memory"]

    facts = ltm.get("facts_learned")
    if not isinstance(facts, list):
        facts = []
    ltm["facts_learned"] = facts

    now = datetime.now().isoformat()
    for cand in candidates:
        key = _normalize_fact_key(cand)
        if not key:
            continue
        found_idx: int | None = None
        for i, item in enumerate(facts):
            t = _fact_text(item)
            if _normalize_fact_key(t) == key:
                found_idx = i
                break
        if found_idx is not None:
            item = facts[found_idx]
            if isinstance(item, dict):
                item["fact"] = cand
                item["seen_count"] = int(item.get("seen_count", 1) or 1) + 1
                item["last_seen"] = now
                item.setdefault("source", "auto")
            else:
                facts[found_idx] = {
                    "fact": cand,
                    "source": "auto",
                    "learned_at": now,
                    "seen_count": 2,
                    "last_seen": now,
                }
            logger.info("Fact reinforced (seen again): %s", cand[:80])
        else:
            facts.append(
                {
                    "fact": cand,
                    "source": "auto",
                    "learned_at": now,
                    "seen_count": 1,
                    "last_seen": now,
                }
            )
            logger.info("New fact learned: %s", cand[:80])

    if len(facts) > MAX_FACTS_LEARNED:
        del facts[: len(facts) - MAX_FACTS_LEARNED]

    return memory_data
