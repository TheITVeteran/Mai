"""
Fact Extraction from user messages.
Identifies and stores declarative user facts (“I work in…”, “I have a cat…”)
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from mai.config import (
    LLM_MAX_OUTPUT_TOKENS,
    LLM_MODEL,
    LLM_REPEAT_PENALTY,
    LLM_TEMPERATURE,
    LLM_USE_SYSTEM_PROMPT,
    REQUEST_TIMEOUT_S,
)
from mai.llm import ChatParams, get_chat_provider
from mai.llm.lmstudio_provider import LMStudioProvider
from mai.llm.types import ChatProvider

logger = logging.getLogger(__name__)


def _is_likely_fact(text: str) -> bool:
    """Quick heuristic to check if text might be a fact."""
    if len(text) < 10:
        return False
    fact_patterns = [
        r"i\s+(work|live|study|have|am|like|love|hate|perfer)",
        r"my\s+(name|job|cat|dog|place|house|apartment|partner|spouse)",
        r"i'm\s+a",
        r"i've\s+ been",
        r"(been|working|living|studying).*(years|months|since)",
    ]
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in fact_patterns)


def extract_facts_nlp(user_message: str) -> list[str]:
    """
    Fast keyword-based fact extraction.
    returns list of facts extracted from the user message.
    """
    if not _is_likely_fact(user_message):
        return []
    facts = []
    text_lower = user_message.lower()

    # Work patterns
    if re.search(r"i\s+(work|job|am)\s+a\s+(\w+)", text_lower):
        match = re.search(
            r"i\s+(?:work\s+(?:as\s+)?a\s+|am\s+a\s+)(\w+)", text_lower
        )
        if match:
            facts.append(f"Works as a {match.group(1)}")

    # Location
    if re.search(r"i\s+live\s+in\s+(\w+)", text_lower):
        match = re.search(r"i\s+live\s+in\s+(\w+)", text_lower)
        if match:
            facts.append(f"Lives in {match.group(1).strip()}")

    # Pets
    if re.search(r"i\s+have\s+a\s+(cat|dog|bird|rabbit|snake)", text_lower):
        match = re.search(r"i\s+have\s+a\s+a([^,.!?]+)", text_lower)
        if match:
            facts.append(f"Has a {match.group().strip()}")

    # Hobby/Interests
    if re.search(r"i\s+(love|like|enjoy|prefer)\s+(\w+)", text_lower):
        match = re.search(r"i\s+(?:love|like|enjoy|prefer)\s+([^,.!?]+)", text_lower)
        if match:
            facts.append(f"Loves {match.group().strip()}")

    # Study/Learning
    if re.search(r"i\s+(?:study|studying|learning)\s+(\w+)", text_lower):
        match = re.search(
            r"i\s+(?:study|studying|learning)\s+([^,.!?]+)", text_lower
        )
        if match:
            facts.append(f"Learning {match.group().strip()}")
    
    # Gender / pronouns
    if re.search(r"i\s+(?:am\s+)?a\s+woman|she/her|i'm\s+a\s+girl|female", text_lower):
        facts.append("Uses she/her pronouns")
    if re.search(r"i\s+(?:am\s+)?a\s+man|he/him|i'm\s+a\s+guy|male", text_lower):
        facts.append("Uses he/him pronouns")

    return facts


def extract_facts_llm(
    user_message: str,
    *,
    llm: Optional[ChatProvider] = None,
    api_url: Optional[str] = None,
) -> list[str]:
    """
    Use LLM to extract facts from the user message.
    returns list of factual statments.
    """
    chat = llm
    if chat is None and api_url is not None:
        chat = LMStudioProvider(api_url=api_url, default_model=LLM_MODEL)
    if chat is None:
        chat = get_chat_provider()
    if not chat.is_available() or not user_message.strip():
        return []
    focus = (
        "work, location, hobbies, pets, relationships, "
        "interests, personal milestones"
    )
    prompt = f"""
        Extract 0-3 factual statements about the person from this message.
        Focus on: {focus}.
        Return ONLY a json array of strings (facts), nothing else.
        Examples:
        "I just got a new job as a software engineer in Portland"
        -> ["Works as a software engineer", "Lives in Portland"]
        "I love playing guitar and I have a cat named Whiskers"
        -> ["Loves playing guitar", "Has a cat named Whiskers"]
        "Just started learning Python for fun"
        -> ["Learning Python"]

        USER MESSAGE: {user_message[:500]}
        Return ONLY the json array, no markdown or extra text.:"""
    try:
        params = ChatParams(
            model=LLM_MODEL,
            user_prompt=prompt,
            system_prompt=None,
            use_system_prompt_field=LLM_USE_SYSTEM_PROMPT,
            max_output_tokens=min(512, LLM_MAX_OUTPUT_TOKENS),
            temperature=LLM_TEMPERATURE,
            repeat_penalty=LLM_REPEAT_PENALTY,
        )
        response_text = chat.complete(params, timeout=float(REQUEST_TIMEOUT_S))
        if not response_text:
            return []

        text = response_text.strip()
        if text.startswith("```"):
            text = text.split("```")[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()

        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [
                str(f).strip()
                for f in parsed
                if f is not None and str(f).strip()
            ]
        return []
    except Exception as e:
        logger.debug("LLM fact extraction failed: %s", e)
        return []


def extract_facts(
    user_message: str,
    use_llm: bool = True,
    *,
    llm: Optional[ChatProvider] = None,
    api_url: Optional[str] = None,
) -> list[str]:
    """
    Extract facts from user message.
    Try LLM first if enabled and configured, otherwise use NLP.
    """
    if use_llm:
        facts = extract_facts_llm(user_message, llm=llm, api_url=api_url)
        if facts:
            return facts

    return extract_facts_nlp(user_message)


def deduplicate_facts(
    existing_facts: list[dict[str, Any]], new_facts: list[str]
) -> list[dict[str, str]]:
    """
    Filter out duplicate facts from new extraction.
    """
    if not existing_facts:
        return [{"fact": f} for f in new_facts]

    existing_texts = {
        f.get("fact", "").lower() for f in existing_facts if isinstance(f, dict)
    }

    result: list[dict[str, str]] = []
    for fact in new_facts:
        fact_lower = fact.lower().strip()
        if not any(
            fact_lower in existing or existing in fact_lower
            for existing in existing_texts
        ):
            result.append({"fact": fact})

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample = (
        "I just got a job as a Python developer in San Francisco "
        "and I have a cat named Luna"
    )
    logger.info("Testing fact extraction on: %s", sample)

    nlp_facts = extract_facts_nlp(sample)
    logger.info("NLT facts: %s", nlp_facts)

    llm_facts = extract_facts_llm(sample)
    logger.info("LLM facts: %s", llm_facts)

    nlp_as_dicts = [{"fact": f} for f in nlp_facts]
    all_facts = deduplicate_facts(nlp_as_dicts, llm_facts)
    logger.info("All facts: %s", all_facts)

    print("Test complete")
