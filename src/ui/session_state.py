"""Helpers for Assistant per-tab session JSON (flat or legacy nested)."""

from __future__ import annotations

from typing import Any


def normalize_tab_session_block(
    data: dict[str, Any],
    *,
    nested_key: str,
    state_keys: tuple[str, ...] = ("template", "design_intent", "question_draft"),
) -> dict[str, Any] | None:
    """
    Accept either flat tab state or legacy ``{nested_key: {...}}`` wrappers.

    Returns the inner UI state dict, or None if unrecognized.
    """
    nested = data.get(nested_key)
    if isinstance(nested, dict) and any(key in nested for key in state_keys):
        return nested
    if any(key in data for key in state_keys):
        return data
    return None
