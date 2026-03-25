"""Tests for mai.lmstudio HTTP helper and parsing."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mai.lmstudio import extract_assistant_text, post_chat


def test_extract_assistant_text_last_message_wins():
    data = {
        "output": [
            {"type": "reasoning", "content": "think"},
            {"type": "message", "content": " first "},
            {"type": "message", "content": "Second reply"},
        ]
    }
    assert extract_assistant_text(data) == "Second reply"


def test_extract_assistant_text_fallback_first_content():
    data = {"output": [{"type": "other", "content": "only"}]}
    assert extract_assistant_text(data) == "only"


def test_extract_assistant_text_missing_output():
    with pytest.raises(ValueError, match="output"):
        extract_assistant_text({})


def test_post_chat_returns_dict():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "output": [{"type": "message", "content": "hi"}],
    }
    mock_resp.raise_for_status = MagicMock()
    with patch("mai.lmstudio.requests.post", return_value=mock_resp) as post:
        out = post_chat("http://localhost/x", {"model": "m", "input": "a"}, timeout=30.0)
    post.assert_called_once()
    assert out["output"][0]["content"] == "hi"
    mock_resp.raise_for_status.assert_called_once()


def test_post_chat_rejects_non_object_json():
    mock_resp = MagicMock()
    mock_resp.json.return_value = ["not", "object"]
    mock_resp.raise_for_status = MagicMock()
    with patch("mai.lmstudio.requests.post", return_value=mock_resp):
        with pytest.raises(ValueError, match="object"):
            post_chat("http://x", {}, timeout=1.0)
