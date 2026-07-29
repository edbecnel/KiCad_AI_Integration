"""Tests for EIE chat workflow."""

from __future__ import annotations

from inference.chat import build_chat_prompt
from ui.chat_supply import build_chat_prompt as supply_build


def test_chat_supply_reexports_inference() -> None:
    assert build_chat_prompt is supply_build
