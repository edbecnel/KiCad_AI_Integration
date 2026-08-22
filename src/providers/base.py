"""Abstract provider contract."""

from __future__ import annotations

from typing import Protocol

from providers.types import ProviderResponse
from utils.config import AppConfig


class BaseProvider(Protocol):
    """Stateless LLM provider — caller supplies conversation messages each call."""

    def send_message(
        self,
        prompt: str,
        *,
        system: str | None = None,
        image: bytes | None = None,
        image_media_type: str = "image/png",
        config: AppConfig | None = None,
    ) -> ProviderResponse:
        """Send a single user message and return the assistant reply."""
        ...

    def send_messages(
        self,
        messages: list[dict[str, object]],
        *,
        system: str | None = None,
        config: AppConfig | None = None,
    ) -> ProviderResponse:
        """Send a multi-turn message list and return the assistant reply."""
        ...
