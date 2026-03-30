"""Tests for mai.vault.emotional_analyzer (NLP mocked; LM path mocked)."""

from __future__ import annotations

import json

import pytest

import mai.vault.emotional_analyzer as ea_module
from mai.config import (
    HARSH_MESSAGE_BOND_PENALTY,
    HARSH_MESSAGE_TRUST_PENALTY,
)
from mai.vault.emotional_analyzer import (
    EmotionalAnalyzer,
    _apply_relationship_caps_and_rules,
    _coerce_secondary_emotions,
    _detect_harsh_message,
    _extract_first_json_object,
)


@pytest.fixture(autouse=True)
def reset_nlp_globals():
    ea_module._NLP_INIT_ATTEMPTED = False
    ea_module._SIA = None
    yield
    ea_module._NLP_INIT_ATTEMPTED = False
    ea_module._SIA = None


@pytest.fixture
def mock_nlp_baseline(monkeypatch: pytest.MonkeyPatch):
    """Deterministic VADER + subjectivity without NLTK/TextBlob."""

    class _SIA:
        def polarity_scores(self, text: str):
            return {"compound": 0.1, "neu": 0.35, "pos": 0.25, "neg": 0.2}

    monkeypatch.setattr(ea_module, "_get_vader", lambda: _SIA())
    monkeypatch.setattr(ea_module, "_textblob_subjectivity", lambda text: 0.55)


def test_empty_user_message_returns_empty_analysis(mock_nlp_baseline):
    a = EmotionalAnalyzer(lmstudio_url="")
    out = a.analyze_interaction("", "hello")
    assert out is not None
    assert out["primary_emotion"] == "neutral"
    assert out["analysis_type"] == "empty"
    assert out["confidence"] == 0.0


def test_whitespace_only_user_treated_empty(mock_nlp_baseline):
    a = EmotionalAnalyzer(lmstudio_url="")
    out = a.analyze_interaction("   \n", "ok")
    assert out["analysis_type"] == "empty"


def test_nlp_fast_path_happy_keyword(mock_nlp_baseline):
    a = EmotionalAnalyzer(lmstudio_url="")
    out = a.analyze_interaction(
        "I feel happy today!", "That's wonderful!", use_deep_analysis=False
    )
    assert out["analysis_type"] == "nlp"
    assert out["primary_emotion"] == "happy"
    assert "valence" in out


def test_nlp_vulnerability_markers(mock_nlp_baseline):
    a = EmotionalAnalyzer(lmstudio_url="")
    out = a.analyze_interaction(
        "Things are difficult lately.", "I'm here.", use_deep_analysis=False
    )
    assert out["vulnerability_marker"] == ["detected"]


def test_should_update_state_lmstudio_threshold():
    a = EmotionalAnalyzer()
    assert a.should_update_state({"confidence": 0.44, "analysis_type": "lmstudio"}) is False
    assert a.should_update_state({"confidence": 0.45, "analysis_type": "lmstudio"}) is True


def test_should_update_state_nlp_threshold():
    a = EmotionalAnalyzer()
    assert a.should_update_state({"confidence": 0.54, "analysis_type": "nlp"}) is False
    assert a.should_update_state({"confidence": 0.55, "analysis_type": "nlp"}) is True


def test_apply_analysis_updates_state(mock_nlp_baseline):
    a = EmotionalAnalyzer(lmstudio_url="")
    analysis = a.analyze_interaction("I love you Mai", "Me too!", use_deep_analysis=False)
    assert analysis is not None
    state: dict = {}
    new_state = a.apply_analysis_to_state(state, analysis)
    es = new_state.get("emotional_state", {})
    assert es.get("primary_emotion") == "affectionate"
    assert "valence" in es
    assert es.get("recent_changes")
    assert isinstance(es["recent_changes"], list)


def test_apply_analysis_skips_low_confidence():
    a = EmotionalAnalyzer()
    base = {"emotional_state": {"primary_emotion": "calm", "valence": 0.9}}
    low = {
        "primary_emotion": "angry",
        "confidence": 0.2,
        "analysis_type": "nlp",
        "secondary_emotions": [],
        "valence": -0.9,
        "arousal": 0.5,
        "dominance": 0.5,
        "intensity": 0.5,
        "triggers": [],
    }
    out = a.apply_analysis_to_state(dict(base), low)
    assert out["emotional_state"]["primary_emotion"] == "calm"


def test_parse_analysis_embedded_json():
    a = EmotionalAnalyzer()
    blob = '{"user_primary_emotion":"joy","user_secondary_emotions":[],"valence":0.5,"arousal":0.5,"dominance":0.5,"intensity":0.5,"confidence":0.9,"triggers":[]}'
    wrapped = f"Here is JSON:\n{blob}\nThanks."
    parsed = a._parse_analysis(wrapped)
    assert parsed is not None
    assert parsed["user_primary_emotion"] == "joy"


def test_merge_analyses_sets_combined(mock_nlp_baseline):
    a = EmotionalAnalyzer(lmstudio_url="")
    nlp = a.analyze_interaction("ok", "ok", use_deep_analysis=False)
    assert nlp is not None
    lm = {
        "user_primary_emotion": "hope",
        "user_secondary_emotions": [],
        "valence": 0.6,
        "arousal": 0.5,
        "dominance": 0.5,
        "intensity": 0.6,
        "confidence": 0.95,
        "triggers": ["x"],
    }
    merged = a._merge_analyses(nlp, a._normalize_analysis(lm))
    assert merged.get("combined") is True
    assert merged["primary_emotion"] == "hope"


def test_lmstudio_path_normalizes(mock_nlp_baseline, monkeypatch: pytest.MonkeyPatch):
    payload = {
        "user_primary_emotion": "relief",
        "user_secondary_emotions": ["exhaustion"],
        "mai_felt_tone": "gentle",
        "mood_digest": "Quiet exhale.",
        "valence": 0.25,
        "arousal": 0.4,
        "dominance": 0.5,
        "intensity": 0.55,
        "confidence": 0.82,
        "triggers": ["done"],
        "sarcasm_detected": False,
        "vulnerability_markers": [],
        "trust_indicators": [],
        "relationship_impact": {
            "trust_shift": 0.0,
            "familiarity_shift": 0.0,
            "bond_strength_shift": 0.0,
        },
        "emotional_arc": "ease",
        "analysis_notes": "",
    }

    def fake_query(self, prompt: str) -> str:
        return json.dumps(payload)

    monkeypatch.setattr(EmotionalAnalyzer, "_query_lmstudio", fake_query)
    a = EmotionalAnalyzer(lmstudio_url="http://fake")
    out = a.analyze_interaction(
        "The week is finally over.", "Rest well.", use_deep_analysis=True
    )
    assert out is not None
    assert out["primary_emotion"] == "relief"
    assert out["analysis_type"] == "lmstudio"
    assert out.get("combined") is True


def test_lmstudio_failure_falls_back_to_nlp(mock_nlp_baseline, monkeypatch: pytest.MonkeyPatch):
    def boom(self, prompt: str) -> str:
        raise RuntimeError("offline")

    monkeypatch.setattr(EmotionalAnalyzer, "_query_lmstudio", boom)
    a = EmotionalAnalyzer(lmstudio_url="http://fake")
    out = a.analyze_interaction(
        "I am happy!", "Nice!", use_deep_analysis=True
    )
    assert out is not None
    assert out["analysis_type"] == "nlp"


def test_recent_changes_truncates():
    a = EmotionalAnalyzer()
    state: dict = {"emotional_state": {"recent_changes": []}}
    analysis_base = {
        "primary_emotion": "neutral",
        "secondary_emotions": [],
        "valence": 0.5,
        "arousal": 0.5,
        "dominance": 0.5,
        "intensity": 0.5,
        "confidence": 0.9,
        "analysis_type": "lmstudio",
        "triggers": [],
        "timestamp": "t",
    }
    for i in range(25):
        hist = dict(analysis_base)
        hist["timestamp"] = f"t{i}"
        state = a.apply_analysis_to_state(state, hist)
    rc = state["emotional_state"]["recent_changes"]
    assert len(rc) == 20
    assert rc[-1]["timestamp"] == "t24"


def test_coerce_secondary_emotions_variants():
    assert _coerce_secondary_emotions({"secondary_emotions": ["A", "B"]}) == ["A", "B"]
    assert _coerce_secondary_emotions({"secondary_emotion": ["x"]}) == ["x"]
    assert _coerce_secondary_emotions({"secondary_emotion": "solo"}) == ["solo"]
    assert _coerce_secondary_emotions({}) == []


def test_extract_first_json_object_nested():
    text = 'noise {"a": {"b": 1}} tail'
    raw = _extract_first_json_object(text)
    assert raw is not None
    assert json.loads(raw) == {"a": {"b": 1}}


def test_fallback_analysis_shape():
    a = EmotionalAnalyzer()
    fb = a._fallback_analysis("hello", "boom")
    assert fb["analysis_type"] == "fallback"
    assert "primary_emotion" in fb


def test_detect_harsh_message():
    assert _detect_harsh_message("I hate you Mai") is True
    assert _detect_harsh_message("Thanks for the help") is False


def test_apply_relationship_caps_preserves_bond_strength_shift_key():
    out = _apply_relationship_caps_and_rules(
        "thanks",
        {"trust_shift": 0.0, "bond_strength_shift": 0.04, "familiarity_shift": 0.0},
    )
    assert "bond_strength_shift" in out
    assert "bond_shift" not in out
    assert out["bond_strength_shift"] == pytest.approx(0.04)


def test_harsh_message_penalty_overrides_mild_positive_shifts():
    out = _apply_relationship_caps_and_rules(
        "I hate you, Mai.",
        {"trust_shift": 0.2, "bond_strength_shift": 0.2, "familiarity_shift": 0.0},
    )
    assert out["trust_shift"] == pytest.approx(HARSH_MESSAGE_TRUST_PENALTY)
    assert out["bond_strength_shift"] == pytest.approx(HARSH_MESSAGE_BOND_PENALTY)


def test_harsh_message_deepens_negative_when_model_was_too_soft():
    out = _apply_relationship_caps_and_rules(
        "I hate you",
        {"trust_shift": -0.02, "bond_strength_shift": -0.02, "familiarity_shift": 0.0},
    )
    assert out["trust_shift"] == pytest.approx(HARSH_MESSAGE_TRUST_PENALTY)
    assert out["bond_strength_shift"] == pytest.approx(HARSH_MESSAGE_BOND_PENALTY)


def test_apply_analysis_updates_bond_strength_from_impact(mock_nlp_baseline):
    a = EmotionalAnalyzer(lmstudio_url="")
    state: dict = {
        "relationship_state": {
            "trust_level": 0.5,
            "bond_strength": 0.5,
            "familiarity": 0.5,
            "total_interactions": 0,
        }
    }
    analysis = {
        "primary_emotion": "neutral",
        "secondary_emotions": [],
        "valence": 0.5,
        "arousal": 0.5,
        "dominance": 0.5,
        "intensity": 0.5,
        "confidence": 0.9,
        "analysis_type": "lmstudio",
        "triggers": [],
        "relationship_impact": {
            "trust_shift": 0.0,
            "bond_strength_shift": 0.06,
            "familiarity_shift": 0.0,
        },
    }
    new_state = a.apply_analysis_to_state(state, analysis, user_message="you're great")
    assert new_state["relationship_state"]["bond_strength"] == pytest.approx(0.56)
