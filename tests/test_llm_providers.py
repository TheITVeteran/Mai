"""Tests for provider-agnostic LLM layer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from mai.llm import ChatParams
from mai.llm.lmstudio_provider import LMStudioProvider
from mai.llm.openai_compatible_provider import OpenAICompatibleProvider


def test_lm_studio_provider_builds_body():
    p = LMStudioProvider(api_url="http://localhost/x", default_model="m")
    with patch("mai.llm.lmstudio_provider.post_chat") as pc:
        pc.return_value = {
            "output": [{"type": "message", "content": " hi "}],
        }
        out = p.complete(
            ChatParams(
                model="m2",
                user_prompt="u",
                system_prompt="s",
                use_system_prompt_field=True,
                max_output_tokens=100,
                temperature=0.5,
                repeat_penalty=1.1,
            ),
            timeout=30.0,
        )
    assert out == "hi"
    body = pc.call_args[0][1]
    assert body["model"] == "m2"
    assert body["system_prompt"] == "s"
    assert body["input"] == "u"
    assert body["max_output_tokens"] == 100


def test_openai_compatible_provider_parses_message():
    p = OpenAICompatibleProvider(
        api_url="http://localhost/v1/chat/completions", default_model="gpt"
    )
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"role": "assistant", "content": "OK"}}]
    }
    with patch(
        "mai.llm.openai_compatible_provider.requests.post", return_value=mock_resp
    ):
        out = p.complete(
            ChatParams(model="gpt-4", user_prompt="hello"),
            timeout=10.0,
        )
    assert out == "OK"


def test_openai_compatible_sends_bearer_when_key_set():
    p = OpenAICompatibleProvider(
        api_url="http://api.example/v1/chat/completions",
        default_model="x",
        api_key="secret",
    )
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "z"}}]
    }
    with patch(
        "mai.llm.openai_compatible_provider.requests.post", return_value=mock_resp
    ) as post:
        p.complete(ChatParams(model="", user_prompt="u"), timeout=1.0)
    headers = post.call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer secret"
