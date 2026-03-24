"""
Hybrid Emotional Analyzer for Mai
Combines both NLP and LLM-based approaches to analyze emotions in conversations.
"""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from mai.config import (
    EMOTION_ANALYSIS_MODE,
    EMOTION_STATE_BLEND,
    LMSTUDIO_API_URL,
    LMSTUDIO_MODEL,
    REQUEST_TIMEOUT_S,
)

logger = logging.getLogger(__name__)

_MAX_USER_CHARS = 8000
_NLP_INIT_ATTEMPTED = False
_SIA = None


def _get_vader() -> Optional[Any]:
    """Lazy VADER; returns None if NLTK / lexicon unavailable."""
    global _NLP_INIT_ATTEMPTED, _SIA
    if _NLP_INIT_ATTEMPTED:
        return _SIA
    _NLP_INIT_ATTEMPTED = True
    try:
        import nltk
        from nltk.sentiment import SentimentIntensityAnalyzer

        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            nltk.download("vader_lexicon", quiet=True)
        _SIA = SentimentIntensityAnalyzer()
    except Exception as e:
        logger.warning("VADER unavailable (%s); valence falls back to neutral.", e)
        _SIA = None
    return _SIA


def _textblob_subjectivity(text: str) -> float:
    try:
        from textblob import TextBlob

        return float(TextBlob(text).sentiment.subjectivity)
    except Exception:
        return 0.5


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _safe_float(value: Any, default: float = 0.5) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _extract_first_json_object(text: str) -> Optional[str]:
    """Return the first balanced {...} substring, or None."""
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _coerce_secondary_emotions(data: Dict[str, Any]) -> List[str]:
    raw = data.get("secondary_emotions")
    if isinstance(raw, list):
        return [str(x) for x in raw if x is not None]
    alt = data.get("secondary_emotion")
    if isinstance(alt, list):
        return [str(x) for x in alt if x is not None]
    if isinstance(alt, str) and alt:
        return [alt]
    return []


class EmotionalAnalyzer:
    """Hybrid NLP + LLM emotional analyzer with graceful degradation."""

    def __init__(self, lmstudio_url: Optional[str] = None, model: Optional[str] = None):
        self.lmstudio_url = (lmstudio_url or LMSTUDIO_API_URL or "").strip()
        self.model = model or LMSTUDIO_MODEL
        self.use_deep_analysis = False

    def _sanitize_message(self, raw: Optional[str], max_chars: int = _MAX_USER_CHARS) -> str:
        if raw is None:
            return ""
        s = str(raw).strip()
        if len(s) > max_chars:
            s = s[:max_chars]
        return s

    def _empty_message_analysis(self) -> Dict[str, Any]:
        now = datetime.now().isoformat()
        return {
            "primary_emotion": "neutral",
            "secondary_emotions": [],
            "valence": 0.0,
            "arousal": 0.0,
            "dominance": 0.5,
            "intensity": 0.0,
            "confidence": 0.0,
            "triggers": [],
            "sarcasm_detected": False,
            "vulnerability_marker": [],
            "trust_indicator": [],
            "relationship_impact": {
                "trust_shift": 0.0,
                "familiarity_shift": 0.0,
                "bond_strength_shift": 0.0,
            },
            "emotional_arc": "no user text",
            "analysis_notes": "empty message",
            "timestamp": now,
            "analysis_type": "empty",
        }

    def analyze_interaction(
        self,
        user_message: str,
        mai_response: str,
        conversation_history: Optional[List[Dict]] = None,
        current_state: Optional[Dict] = None,
        use_deep_analysis: Optional[bool] = None,
    ) -> Optional[Dict]:
        """
        Analyze affect for the user message + Mai's reply.

        ``use_deep_analysis``:
        - ``True`` / ``False``: force LM Studio on or off (if URL set).
        - ``None``: use ``EMOTION_ANALYSIS_MODE`` (fast / hybrid / llm).
        """
        user_message = self._sanitize_message(user_message)
        mai_response = self._sanitize_message(mai_response)

        if not user_message:
            return self._empty_message_analysis()

        try:
            analysis = self._nlp_analysis(user_message)

            run_llm: bool
            if use_deep_analysis is True:
                run_llm = bool(self.lmstudio_url)
            elif use_deep_analysis is False:
                run_llm = False
            elif EMOTION_ANALYSIS_MODE == "llm":
                run_llm = bool(self.lmstudio_url)
            elif EMOTION_ANALYSIS_MODE == "hybrid":
                run_llm = bool(self.lmstudio_url) and self._should_deep_analyze(
                    user_message, analysis
                )
            else:
                run_llm = False

            if run_llm:
                deep = self._lmstudio_analysis(
                    user_message,
                    mai_response,
                    conversation_history,
                    current_state,
                )
                if deep:
                    analysis = self._merge_analyses(analysis, deep)
                else:
                    analysis = self._normalize_analysis(analysis)
            else:
                analysis = self._normalize_analysis(analysis)

            return analysis
        except Exception as e:
            logger.exception("Emotional analysis failed: %s", e)
            return self._fallback_analysis(user_message, str(e))

    def _should_deep_analyze(
        self, user_message: str, nlp_analysis: Dict[str, Any]
    ) -> bool:
        """Heuristic: use LM Studio on emotionally loaded or complex turns."""
        if len(user_message) >= 180:
            return True
        if nlp_analysis.get("vulnerability_marker"):
            return True
        if nlp_analysis.get("trust_indicator"):
            return True
        if abs(_safe_float(nlp_analysis.get("valence"), 0.0)) >= 0.45:
            return True
        if _safe_float(nlp_analysis.get("intensity"), 0.5) >= 0.62:
            return True
        if nlp_analysis.get("sarcasm_detected"):
            return True
        return False

    def _fallback_analysis(self, user_message: str, reason: str) -> Dict[str, Any]:
        """Keyword-only snapshot when NLP / merge fails."""
        primary = self._detect_emotion_keywords(user_message)
        now = datetime.now().isoformat()
        return {
            "primary_emotion": primary,
            "secondary_emotions": [],
            "valence": 0.0,
            "arousal": 0.5,
            "dominance": 0.5,
            "intensity": 0.5,
            "confidence": 0.35,
            "triggers": [],
            "sarcasm_detected": False,
            "vulnerability_marker": [],
            "trust_indicator": [],
            "relationship_impact": {
                "trust_shift": 0.0,
                "familiarity_shift": 0.0,
                "bond_strength_shift": 0.0,
            },
            "emotional_arc": "fallback",
            "analysis_notes": f"fallback: {reason[:200]}",
            "timestamp": now,
            "analysis_type": "fallback",
        }

    def _nlp_analysis(self, user_message: str) -> Dict[str, Any]:
        """Fast NLP-based emotional analysis."""
        sia = _get_vader()
        if sia is not None:
            vader = sia.polarity_scores(user_message)
            valence = float(vader.get("compound", 0.0))
            neu = float(vader.get("neu", 0.5))
        else:
            valence = 0.0
            neu = 0.5

        subjectivity = _textblob_subjectivity(user_message)
        primary_emotion = self._detect_emotion_keywords(user_message)
        vulnerability = self._has_vulnerability_markers(user_message)
        trust = self._has_trust_indicators(user_message)
        sarcasm = self._detect_sarcasm(user_message)

        return {
            "primary_emotion": primary_emotion,
            "secondary_emotions": [],
            "valence": valence,
            "arousal": subjectivity,
            "dominance": 0.5,
            "intensity": _clamp(1.0 - neu, 0.0, 1.0),
            "confidence": 0.7 if sia is not None else 0.45,
            "triggers": [],
            "sarcasm_detected": sarcasm,
            "vulnerability_marker": ["detected"] if vulnerability else [],
            "trust_indicator": ["detected"] if trust else [],
            "relationship_impact": {
                "trust_shift": 0.05 if trust else 0.0,
                "familiarity_shift": 0.02,
                "bond_strength_shift": 0.05 if vulnerability else 0.0,
            },
            "emotional_arc": "analyzing sentiment",
            "analysis_notes": (
                f"NLP analysis - subjectivity: {subjectivity:.2f}"
                + ("" if sia is not None else " (VADER unavailable)")
            ),
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "nlp",
        }

    def _detect_emotion_keywords(self, text: str) -> str:
        """Simple keyword-based emotion detection."""
        if not text:
            return "neutral"
        text_lower = text.lower()

        # Broad buckets + social / blended affects (first match wins; order matters)
        emotion_keywords = {
            "happy": [
                "happy", "joyful", "excited", "ecstatic", "delighted",
                "pleased", "content", "satisfied", "grateful", "thankful",
                "blessed", "relieved", "hopeful", "optimistic", "proud",
            ],
            "affectionate": [
                "love you", "miss you", "care about", "hug", "cuddle",
                "sweetheart", "darling", "closer to you",
            ],
            "lonely": [
                "lonely", "alone", "isolated", "no one", "abandoned",
                "ignored", "ghosted",
            ],
            "jealous": [
                "jealous", "envy", "envious", "replaced", "someone else",
                "not enough", "compared",
            ],
            "guilty": [
                "guilty", "ashamed", "sorry i", "my fault", "shouldn't have",
                "regret", "embarrassed",
            ],
            "sad": [
                "sad", "depressed", "miserable", "unhappy", "disappointed",
                "regretful", "sorrowful", "dejected", "grief", "crying",
                "tears", "heartbroken", "numb", "empty inside",
            ],
            "angry": [
                "angry", "irritated", "frustrated", "annoyed", "aggravated",
                "resentful", "enraged", "furious", "hate you", "pissed",
            ],
            "fearful": [
                "fearful", "anxious", "nervous", "scared", "terrified",
                "frightened", "panicked", "horrified", "worried sick",
                "overwhelmed", "can't cope", "breaking down",
            ],
            "surprised": [
                "surprised", "shocked", "astonished", "amazed", "gobsmacked",
                "flabbergasted", "stupefied", "dumbfounded", "didn't expect",
            ],
            "disgusted": [
                "disgusted", "repulsed", "revolted", "disgusting", "offended",
                "sickened",
            ],
            "nostalgic": [
                "nostalgic", "remember when", "used to", "back then",
                "good old days", "miss those",
            ],
            "conflicted": [
                "conflicted", "mixed feelings", "on the fence", "not sure",
                "part of me", "but also",
            ],
            "neutral": [],
        }

        for emotion, keywords in emotion_keywords.items():
            if emotion == "neutral":
                continue
            if any(kw in text_lower for kw in keywords):
                return emotion
        return "neutral"

    def _has_vulnerability_markers(self, text: str) -> bool:
        if not text:
            return False
        markers = [
            "struggle", "difficult", "hard", "pain", "hurt",
            "scared", "afraid", "worried", "anxious",
            "help", "support", "need you", "thanks",
        ]
        text_lower = text.lower()
        return any(m in text_lower for m in markers)

    def _has_trust_indicators(self, text: str) -> bool:
        if not text:
            return False
        indicators = [
            "share", "tell you", "advice", "what do you think",
            "help", "trust", "believe", "honestly", "really",
        ]
        text_lower = text.lower()
        return any(ind in text_lower for ind in indicators)

    def _detect_sarcasm(self, text: str) -> bool:
        if not text:
            return False
        text_lower = text.lower()
        has_exclamation = "!" in text
        negative_words = ["hate", "terrible", "awful", "worst"]
        has_negative = any(word in text_lower for word in negative_words)
        return has_exclamation and has_negative

    def _lmstudio_analysis(
        self,
        user_message: str,
        mai_response: str,
        conversation_history: Optional[List[Dict]] = None,
        current_state: Optional[Dict] = None,
    ) -> Optional[Dict]:
        try:
            prompt = self._build_analysis_prompt(
                user_message,
                mai_response,
                conversation_history,
                current_state,
            )
            analysis_text = self._query_lmstudio(prompt)
            if not analysis_text:
                return None
            analysis = self._parse_analysis(analysis_text)
            if analysis:
                analysis = self._normalize_analysis(analysis)
                analysis["analysis_type"] = "lmstudio"
            return analysis
        except Exception as e:
            logger.warning("Deep LM Studio analysis failed: %s", e)
            return None

    def _build_analysis_prompt(
        self,
        user_message: str,
        mai_response: str,
        conversation_history: Optional[List[Dict]] = None,
        current_state: Optional[Dict] = None,
    ) -> str:
        context = ""

        if conversation_history:
            context += "Conversation history:\n"
            recent = (
                conversation_history[-6:]
                if len(conversation_history) > 6
                else conversation_history
            )
            for interaction in recent:
                if not isinstance(interaction, dict):
                    continue
                user_msg = str(interaction.get("user_message", ""))[:80]
                mai_msg = str(interaction.get("mai_response", ""))[:80]
                context += f" - User: {user_msg}\n   Mai: {mai_msg}\n"

        if current_state and isinstance(current_state, dict):
            es = current_state.get("emotional_state") or {}
            if not isinstance(es, dict):
                es = {}
            current_emotion = es.get("primary_emotion", "neutral")
            cv = _safe_float(es.get("valence"), 0.5)
            context += (
                f"\nCURRENT STATE: {current_emotion} (valence: {cv:.2f})\n"
            )

        um = user_message.replace('"', "'")[:2000]
        mr = str(mai_response).replace('"', "'")[:2000]

        return f"""You are an affective inference engine for "Mai", a companion who cares deeply.
Infer nuanced, human-like emotional states from the USER's message and Mai's reply — including mixed or social emotions (e.g. grateful-but-exhausted, warm-but-worried).

Use this vocabulary when it fits (not exhaustive): joy, sadness, fear, anger, surprise, disgust, love, affection, longing, jealousy, guilt, shame, pride, hope, relief, loneliness, overwhelm, numbness, bittersweet, trust, hurt, tenderness, playfulness, defensiveness, vulnerability.

CONVERSATION:
User: "{um}"
Mai's reply: "{mr}"
{context}

Return ONE JSON object only (no markdown). Fields:
- user_primary_emotion: short label for the user's dominant affect
- user_secondary_emotions: 0-4 additional labels (blends welcome)
- mai_felt_tone: 1-2 phrases — how Mai would *feel toward the user* this beat (empathic stance, not clinical)
- mood_digest: one vivid sentence: Mai's internal mood *right now* for diary / memory
- valence: -1 very negative .. 1 very positive (user-anchored)
- arousal: 0 calm .. 1 activated
- dominance: 0 submissive/withdrawn .. 1 assertive/in-control
- intensity: 0 flat .. 1 overwhelming
- confidence: 0..1 how sure you are
- triggers: short phrases from the text that drove the read
- sarcasm_detected: boolean
- vulnerability_markers: short phrases if user opened up
- trust_indicators: short phrases if bonding / reliance showed
- relationship_impact: {{"trust_shift": -0.1..0.1, "familiarity_shift": -0.1..0.1, "bond_strength_shift": -0.1..0.1}}
- emotional_arc: one line (e.g. "softens after tension")
- analysis_notes: brief clinician-style note (optional)

Example shape:
{{"user_primary_emotion":"bittersweet","user_secondary_emotions":["relief","exhaustion"],"mai_felt_tone":"warm, protective, a little worried","mood_digest":"She wants closeness but sounds drained; Mai leans caring.","valence":0.2,"arousal":0.55,"dominance":0.45,"intensity":0.65,"confidence":0.78,"triggers":["struggling","talking helps"],"sarcasm_detected":false,"vulnerability_markers":["struggling lately"],"trust_indicators":["talking to you helps"],"relationship_impact":{{"trust_shift":0.06,"familiarity_shift":0.03,"bond_strength_shift":0.07}},"emotional_arc":"vulnerability met with reassurance","analysis_notes":"High intimacy cue; stable positive valence."}}
"""

    def _query_lmstudio(self, prompt: str) -> str:
        """POST to LM Studio; raises on HTTP/JSON/shape errors."""
        payload = {"model": self.model, "input": prompt}
        response = requests.post(
            self.lmstudio_url,
            json=payload,
            timeout=REQUEST_TIMEOUT_S,
        )
        response.raise_for_status()
        data = response.json()
        out = data.get("output")
        if not isinstance(out, list) or len(out) == 0:
            raise ValueError("LM Studio response missing output[]")
        first = out[0]
        if isinstance(first, dict):
            content = first.get("content")
        else:
            content = first
        if content is None:
            raise ValueError("LM Studio output item missing content")
        return str(content)

    def _parse_analysis(self, analysis_text: str) -> Optional[Dict[str, Any]]:
        if not analysis_text or not str(analysis_text).strip():
            return None
        text = str(analysis_text).strip()
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            pass
        blob = _extract_first_json_object(text)
        if blob:
            try:
                parsed = json.loads(blob)
                return parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                return None
        return None

    def _normalize_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(analysis)
        upe = out.get("user_primary_emotion")
        if upe is not None and str(upe).strip():
            out["primary_emotion"] = str(upe).strip().lower()
        elif not str(out.get("primary_emotion", "")).strip():
            out["primary_emotion"] = "neutral"
        else:
            out["primary_emotion"] = str(out["primary_emotion"]).strip().lower()

        sec = out.get("user_secondary_emotions")
        if isinstance(sec, list):
            out["secondary_emotions"] = [
                str(x).strip().lower() for x in sec if x is not None and str(x).strip()
            ]
        else:
            out["secondary_emotions"] = _coerce_secondary_emotions(out)

        for key in ("mai_felt_tone", "mood_digest"):
            if key in out and out[key] is not None:
                out[key] = str(out[key]).strip()[:600]

        out["valence"] = _clamp(_safe_float(out.get("valence"), 0.5), -1.0, 1.0)
        out["arousal"] = _clamp(_safe_float(out.get("arousal"), 0.5), 0.0, 1.0)
        out["dominance"] = _clamp(_safe_float(out.get("dominance"), 0.5), 0.0, 1.0)
        out["intensity"] = _clamp(_safe_float(out.get("intensity"), 0.5), 0.0, 1.0)
        out["confidence"] = _clamp(_safe_float(out.get("confidence"), 0.5), 0.0, 1.0)
        triggers = out.get("triggers", [])
        out["triggers"] = triggers if isinstance(triggers, list) else []
        out["timestamp"] = datetime.now().isoformat()
        return out

    def _merge_analyses(
        self, nlp_analysis: Dict[str, Any], lmstudio_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        merged = deepcopy(nlp_analysis)
        lm = deepcopy(lmstudio_analysis)
        merged.update(lm)
        merged["confidence"] = lm.get("confidence", nlp_analysis.get("confidence", 0.5))
        merged["combined"] = True
        return self._normalize_analysis(merged)

    def should_update_state(self, analysis: Dict[str, Any]) -> bool:
        confidence = _safe_float(analysis.get("confidence"), 0.0)
        at = str(analysis.get("analysis_type", ""))
        if at in ("lmstudio", "combined"):
            return confidence >= 0.45
        return confidence >= 0.55

    def apply_analysis_to_state(
        self, state_data: Dict[str, Any], analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not analysis or not isinstance(analysis, dict):
            return state_data
        if not self.should_update_state(analysis):
            return state_data

        if not isinstance(state_data, dict):
            state_data = {}

        if "emotional_state" not in state_data or not isinstance(
            state_data["emotional_state"], dict
        ):
            state_data["emotional_state"] = {}

        es = state_data["emotional_state"]

        alpha = EMOTION_STATE_BLEND
        conf = _safe_float(analysis.get("confidence"), 0.0)
        at = str(analysis.get("analysis_type", ""))
        new_primary = str(analysis.get("primary_emotion", "neutral"))
        if conf >= 0.52 or at in ("lmstudio", "combined"):
            es["primary_emotion"] = new_primary
        else:
            es["primary_emotion"] = es.get("primary_emotion", new_primary)

        es["secondary_emotions"] = _coerce_secondary_emotions(analysis)

        def _blend(key: str, default: float = 0.5) -> None:
            new_v = _safe_float(analysis.get(key), default)
            if alpha > 0 and key in es:
                old = _safe_float(es.get(key), new_v)
                es[key] = (1.0 - alpha) * old + alpha * new_v
            else:
                es[key] = new_v

        _blend("valence", 0.5)
        _blend("arousal", 0.5)
        _blend("dominance", 0.5)
        _blend("intensity", 0.5)
        es["confidence"] = _safe_float(analysis.get("confidence"), 0.5)

        mood = analysis.get("mood_digest") or analysis.get("mood")
        if mood and str(mood).strip():
            es["mood"] = str(mood).strip()[:500]
        mft = analysis.get("mai_felt_tone")
        if mft and str(mft).strip():
            es["mai_felt_tone"] = str(mft).strip()[:300]

        if "recent_changes" not in es or not isinstance(es["recent_changes"], list):
            es["recent_changes"] = []

        es["recent_changes"].append(
            {
                "timestamp": analysis.get("timestamp"),
                "triggers": analysis.get("triggers", [])
                if isinstance(analysis.get("triggers"), list)
                else [],
                "confidence": _safe_float(analysis.get("confidence"), 0.0),
                "new_emotion": analysis.get("primary_emotion"),
                "analysis_type": analysis.get("analysis_type", "unknown"),
            }
        )

        if len(es["recent_changes"]) > 20:
            es["recent_changes"] = es["recent_changes"][-20:]

        state_data["timestamp"] = datetime.now().isoformat()
        return state_data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    analyzer = EmotionalAnalyzer()
    test = "I've been struggling a lot lately, but talking to you helps"

    print("Hybrid Emotional Analyzer Test\n")

    print("Fast NLP Analysis (instant):")
    result = analyzer.analyze_interaction(test, "I'm here for you.")
    if result:
        print(f" - Primary Emotion: {result['primary_emotion']}")
        print(f" - Valence: {result['valence']:.2f}")
        print(f" - Type: {result['analysis_type']}")

    print("\nDeep LM Studio Analysis (optional):")
    result = analyzer.analyze_interaction(
        test, "I'm here for you.", use_deep_analysis=True
    )
    if result:
        print(f" - Primary Emotion: {result['primary_emotion']}")
        print(f" - Valence: {result['valence']:.2f}")
        print(f" - Type: {result['analysis_type']}")
        if result.get("analysis_type") != "lmstudio" and not result.get("combined"):
            print(" - (LM Studio did not return a mergeable result; NLP only.)")
    else:
        print(" - No result (unexpected failure)")
