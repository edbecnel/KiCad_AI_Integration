"""Tests for provider factory."""

from __future__ import annotations

from providers.claude import ClaudeProvider
from providers.factory import get_provider
from providers.ollama import OllamaProvider
from utils.config import AppConfig


def test_get_provider_returns_claude_by_default() -> None:
    provider = get_provider(AppConfig())
    assert isinstance(provider, ClaudeProvider)


def test_get_provider_returns_ollama_when_configured() -> None:
    provider = get_provider(AppConfig(ai_provider="ollama"))
    assert isinstance(provider, OllamaProvider)
