"""Abstract provider contract."""

from __future__ import annotations

from typing import Protocol

from providers.types import ProviderResponse
from utils.config import AppConfig


class BaseProvider(Protocol):
    """Stateless LLM provider — caller supplies full prompt each call."""

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
