"""Tests for Ollama provider."""

from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import MagicMock

from providers.ollama import OllamaProvider
from utils.config import AppConfig


def test_ollama_send_messages_parses_response() -> None:
    payload = {
        "model": "llama3.2",
        "message": {"role": "assistant", "content": "hello"},
        "prompt_eval_count": 12,
        "eval_count": 5,
        "done_reason": "stop",
    }

    def opener(request, timeout):
        assert request.full_url.endswith("/api/chat")
        body = json.loads(request.data.decode("utf-8"))
        assert body["model"] == "llama3.2"
        assert body["messages"][0]["role"] == "system"
        return BytesIO(json.dumps(payload).encode("utf-8"))

    provider = OllamaProvider(
        AppConfig(ai_provider="ollama", ollama_model="llama3.2"),
        opener=opener,
    )
    response = provider.send_messages(
        [{"role": "user", "content": "hi"}],
        system="You are helpful.",
    )
    assert response.text == "hello"
    assert response.usage.input_tokens == 12
    assert response.usage.output_tokens == 5
