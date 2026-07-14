"""Provider factory."""

from __future__ import annotations

from providers.base import BaseProvider
from providers.claude import ClaudeProvider
from providers.errors import ProviderError
from utils.config import AppConfig, load_config


def get_provider(config: AppConfig | None = None) -> BaseProvider:
    """Return the configured AI provider implementation."""
    cfg = config or load_config()
    if cfg.ai_provider == "claude":
        return ClaudeProvider(cfg)
    raise ProviderError(f"Unsupported AI provider: {cfg.ai_provider!r}")
