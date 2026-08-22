"""Rough USD cost estimates for provider token usage (display only)."""

from __future__ import annotations

# USD per 1M tokens (input, output) — approximate list prices for common models.
_MODEL_RATES: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-20250514": (3.0, 15.0),
    "claude-3-5-sonnet-20241022": (3.0, 15.0),
    "claude-3-5-sonnet-latest": (3.0, 15.0),
    "claude-3-5-haiku-20241022": (0.8, 4.0),
    "claude-3-opus-20240229": (15.0, 75.0),
}

_DEFAULT_RATES = (3.0, 15.0)


def estimate_cost_usd(
    model: str | None,
    input_tokens: int | None,
    output_tokens: int | None,
) -> float | None:
    """Return an approximate USD cost for a single request, or None when unknown."""
    if input_tokens is None or output_tokens is None:
        return None
    in_rate, out_rate = _MODEL_RATES.get(model or "", _DEFAULT_RATES)
    return (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000
