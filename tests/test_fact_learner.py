"""Tests for heuristic fact learning."""

from __future__ import annotations

import pytest

import mai.vault.fact_learner as fl
from mai.vault.fact_learner import (
    extract_declarative_facts,
    merge_learned_facts_from_user_message,
)


def test_extract_name_and_work():
    facts = extract_declarative_facts("My name is Jordan and I work as a barista downtown.")
    assert "Their name is Jordan" in facts
    assert any("They work as a barista downtown" in f for f in facts)


def test_extract_have_pet():
    facts = extract_declarative_facts("I have a black cat named Void.")
    assert facts == ["They have a black cat named Void"]


def test_skip_short_and_questions():
    assert extract_declarative_facts("Hi") == []
    assert extract_declarative_facts("Do I have a cat? What do you think?") == []


def test_skip_command_prefix():
    assert extract_declarative_facts("!remind I have a dog") == []
    assert extract_declarative_facts("/roll I live in Paris") == []


def test_skip_mood_only_im():
    assert extract_declarative_facts("I'm feeling really tired today honestly") == []


def test_merge_dedupes_and_counts(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(fl, "FACT_LEARN_ENABLED", True)
    mem: dict = {"long_term_memory": {"facts_learned": []}}
    m = merge_learned_facts_from_user_message(mem, "I live in Portland.")
    facts = m["long_term_memory"]["facts_learned"]
    assert len(facts) == 1
    assert facts[0]["fact"] == "They live in Portland"
    assert facts[0]["seen_count"] == 1

    m2 = merge_learned_facts_from_user_message(m, "I live in Portland.")
    facts2 = m2["long_term_memory"]["facts_learned"]
    assert len(facts2) == 1
    assert facts2[0]["seen_count"] == 2
    assert "last_seen" in facts2[0]


def test_merge_respects_disabled(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(fl, "FACT_LEARN_ENABLED", False)
    mem: dict = {"long_term_memory": {"facts_learned": []}}
    m = merge_learned_facts_from_user_message(mem, "My name is Alex.")
    assert m["long_term_memory"]["facts_learned"] == []


def test_merge_truncates_cap(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(fl, "FACT_LEARN_ENABLED", True)
    monkeypatch.setattr(fl, "MAX_FACTS_LEARNED", 3)
    mem: dict = {"long_term_memory": {"facts_learned": []}}
    for i in range(5):
        mem = merge_learned_facts_from_user_message(
            mem, f"My name is Person{i} and I am very unique about it {i}."
        )
    facts = mem["long_term_memory"]["facts_learned"]
    assert len(facts) == 3
    joined = " ".join(f["fact"] for f in facts)
    assert "Person4" in joined


def test_i_have_no_idea_skipped():
    assert extract_declarative_facts("I have no idea what you mean, sorry.") == []
