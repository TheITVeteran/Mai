"""
Trim common \"double reply\" artifacts from one LM generation.

RP models often append a second beat (new stage line + new excitement). Discord
still shows a single message — we keep the first coherent segment.
"""

from __future__ import annotations

import re

_RP_VERBS: tuple[str, ...] = (
    "beams",
    "twirls",
    "leans",
    "chuckles",
    "smiles",
    "grins",
    "sighs",
    "blinks",
    "nods",
    "winks",
    "giggles",
    "laughs",
    "frowns",
    "pouts",
    "gasps",
    "blushes",
    "shrugs",
    "tilts",
    "bounces",
    "rests",
    "crosses",
    "claps",
    "pumps",
    "covers",
    "throws",
    "wraps",
    "pulls",
    "reaches",
    "snuggles",
    "hugs",
    "squeals",
    "perks",
    "lights up",
)


def _verb_regex_alternation(verbs: tuple[str, ...]) -> str:
    parts: list[str] = []
    for v in verbs:
        if " " in v:
            parts.append(re.escape(v).replace(r"\ ", r"\s+"))
        else:
            parts.append(re.escape(v))
    return "|".join(parts)


# Punctuation ending the good paragraph, then optional */space/newline, stage verb.
_STAGE_START = re.compile(
    rf"(?P<punc>[.!?])(?P<gap>\s*)(?:\*{{1,2}}\s*)?(?P<v>{_verb_regex_alternation(_RP_VERBS)})\b",
    re.IGNORECASE,
)

_IM_SO = re.compile(r"\bI'm so\b", re.IGNORECASE)
_OH_MY = re.compile(r"\bOh my gosh\b|\bOh my god\b|\bOh wow\b", re.IGNORECASE)

# Model starts over as if a new turn ("Hey there!", "So what's this…") after a finished beat.
_PARAGRAPH_RESTART = re.compile(
    r"(?<=[.!?])(?:(?:\s*\n){1,5}|(?: {2,}))(?:"
    r"Hey there\b|Hi there\b|Hello again\b|"
    r"So,? what's\b|"
    r"I'm curious\b|"
    r"Spill the beans\b"
    r")",
    re.IGNORECASE,
)

# Director's-note lines models leak: "(Playful and eager, leaning into...)" whole line.
_TRAILING_PAREN_STAGE = re.compile(r"\s+\([A-Z][^()]{12,}\)\s*$")


def strip_stage_parentheticals(text: str) -> str:
    """
    Remove out-of-character parenthetical acting notes (whole lines or glued suffix).

    Keeps short chatty parens like ``(lol)``; drops long ``(Adjective, clause...)``
    lines typical of leaked stage directions.
    """
    if not text or not text.strip():
        return text
    out_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if (
            len(stripped) >= 3
            and stripped.startswith("(")
            and stripped.endswith(")")
        ):
            inner = stripped[1:-1].strip()
            if len(inner) >= 15:
                continue
        out_lines.append(line)
    s = "\n".join(out_lines).strip()
    s = _TRAILING_PAREN_STAGE.sub("", s)
    return s.strip()


def _cut_before_second_match(text: str, pat: re.Pattern, min_cut: int) -> str:
    matches = list(pat.finditer(text))
    if len(matches) >= 2 and matches[1].start() >= min_cut:
        return text[: matches[1].start()].rstrip()
    return text


def _cut_at_first(text: str, pat: re.Pattern, min_start: int) -> str:
    m = pat.search(text)
    if m is not None and m.start() >= min_start:
        return text[: m.start()].rstrip()
    return text


def sanitize_mai_reply(text: str, *, min_chars_before_cut: int = 50) -> str:
    """Drop a trailing second \"scene\" if detectors fire."""
    if not text or not text.strip():
        return text
    s = strip_stage_parentheticals(text.strip())

    m = _STAGE_START.search(s)
    if m is not None and m.start("punc") >= min_chars_before_cut:
        s = s[: m.start("punc") + 1].rstrip()

    s = _cut_before_second_match(s, _OH_MY, min_cut=90)
    s = _cut_before_second_match(s, _IM_SO, min_cut=90)
    s = _cut_at_first(s, _PARAGRAPH_RESTART, min_start=90)

    return s.strip()
