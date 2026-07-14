"""Provider-layer error types for UI and CLI display."""

from __future__ import annotations


class ProviderError(Exception):
    """Base class for provider failures."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AuthError(ProviderError):
    """API key missing or rejected."""


class RateLimitError(ProviderError):
    """Provider rate limit exceeded."""


class TimeoutError(ProviderError):
    """Request timed out waiting for the provider."""


class MalformedResponseError(ProviderError):
    """Response body could not be parsed or lacked expected content."""
