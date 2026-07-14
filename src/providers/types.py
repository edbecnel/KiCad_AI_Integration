"""Shared types for AI provider responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ProviderKind(str, Enum):
    """Supported AI provider backends."""

    CLAUDE = "claude"


@dataclass
class TokenUsage:
    """Token counts returned by the provider API."""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class ProviderResponse:
    """Normalized response from any provider implementation."""

    text: str
    model: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    stop_reason: str | None = None
    raw: dict | None = None
