"""Tests for Claude provider (mocked HTTP)."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
import urllib.error

from providers.claude import ClaudeProvider
from providers.errors import AuthError, MalformedResponseError, RateLimitError, TimeoutError
from providers.factory import get_provider
from utils.config import AppConfig

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "anthropic"


def _config(**overrides: object) -> AppConfig:
    return AppConfig(anthropic_api_key="test-key", **overrides)  # type: ignore[arg-type]


def _success_payload() -> dict:
    return json.loads((_FIXTURES / "messages_success.json").read_text(encoding="utf-8"))


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self, size: int = -1) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        pass


def _opener_for_json(data: dict):
    body = json.dumps(data).encode("utf-8")

    def opener(request, timeout=None):
        assert request.get_method() == "POST"
        assert request.full_url == "https://api.anthropic.com/v1/messages"
        assert request.data is not None
        return _FakeResponse(body)

    return opener


def test_send_message_success_text() -> None:
    provider = ClaudeProvider(_config(), opener=_opener_for_json(_success_payload()))
    response = provider.send_message("Summarize the schematic.")
    assert "12 active parts" in response.text
    assert response.usage.input_tokens == 150
    assert response.usage.output_tokens == 28
    assert response.model == "claude-3-5-sonnet-20241022"


def test_send_message_multimodal_includes_image_block() -> None:
    captured: dict = {}

    def opener(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse(json.dumps(_success_payload()).encode("utf-8"))

    provider = ClaudeProvider(_config(), opener=opener)
    image = b"\x89PNG\r\n\x1a\nfake"
    provider.send_message("Describe this schematic.", image=image)

    content = captured["body"]["messages"][0]["content"]
    assert isinstance(content, list)
    assert content[0]["type"] == "image"
    assert content[0]["source"]["media_type"] == "image/png"
    assert content[1]["type"] == "text"
    assert content[1]["text"] == "Describe this schematic."


def test_send_messages_multi_turn() -> None:
    captured: dict = {}

    def opener(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse(json.dumps(_success_payload()).encode("utf-8"))

    provider = ClaudeProvider(_config(), opener=opener)
    messages = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "reply"},
        {"role": "user", "content": "second"},
    ]
    provider.send_messages(messages, system="sys")

    assert captured["body"]["messages"] == messages
    assert captured["body"]["system"] == "sys"


def test_missing_api_key_raises_auth_error() -> None:
    provider = ClaudeProvider(AppConfig(anthropic_api_key=None))
    with pytest.raises(AuthError, match="API key"):
        provider.send_message("hello")


def test_http_401_raises_auth_error() -> None:
    def opener(request, timeout):
        raise urllib.error.HTTPError(
            request.full_url,
            401,
            "Unauthorized",
            hdrs=None,
            fp=BytesIO(b'{"error":{"message":"invalid x-api-key"}}'),
        )

    provider = ClaudeProvider(_config(), opener=opener)
    with pytest.raises(AuthError, match="invalid x-api-key"):
        provider.send_message("hello")


def test_http_429_raises_rate_limit_error() -> None:
    def opener(request, timeout):
        raise urllib.error.HTTPError(
            request.full_url,
            429,
            "Too Many Requests",
            hdrs=None,
            fp=BytesIO(b'{"error":{"message":"rate limited"}}'),
        )

    provider = ClaudeProvider(_config(), opener=opener)
    with pytest.raises(RateLimitError, match="rate limited"):
        provider.send_message("hello")


def test_empty_content_raises_malformed_response() -> None:
    payload = _success_payload()
    payload["content"] = []
    provider = ClaudeProvider(_config(), opener=_opener_for_json(payload))
    with pytest.raises(MalformedResponseError, match="no text blocks"):
        provider.send_message("hello")


def test_non_json_response_raises_malformed_response() -> None:
    def opener(request, timeout):
        return _FakeResponse(b"not-json")

    provider = ClaudeProvider(_config(), opener=opener)
    with pytest.raises(MalformedResponseError, match="non-JSON"):
        provider.send_message("hello")


def test_url_timeout_raises_provider_timeout() -> None:
    def opener(request, timeout):
        raise urllib.error.URLError("timed out")

    provider = ClaudeProvider(_config(), opener=opener)
    with pytest.raises(TimeoutError, match="timed out"):
        provider.send_message("hello")


def test_get_provider_returns_claude() -> None:
    provider = get_provider(_config())
    assert isinstance(provider, ClaudeProvider)


def test_system_prompt_included_in_payload() -> None:
    captured: dict = {}

    def opener(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse(json.dumps(_success_payload()).encode("utf-8"))

    provider = ClaudeProvider(_config(), opener=opener)
    provider.send_message("question", system="You are a PCB engineer.")
    assert captured["body"]["system"] == "You are a PCB engineer."
