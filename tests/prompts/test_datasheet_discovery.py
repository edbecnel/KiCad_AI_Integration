"""Tests for datasheet discovery prompt template."""

from __future__ import annotations

from prompts.templates.datasheet_discovery import build_datasheet_discovery_prompt


def test_prompt_includes_onsemi_direct_pdf_pattern() -> None:
    _user, system = build_datasheet_discovery_prompt({"value": "BD243C"}, max_urls=3)
    assert "onsemi.com/download/data-sheet/pdf" in system
    assert "bd243b-d.pdf" in system
    assert "notFound=" in system


def test_prompt_user_asks_for_direct_pdf_only() -> None:
    user, _system = build_datasheet_discovery_prompt({"value": "BD243C"}, max_urls=3)
    assert "ends in .pdf" in user.lower()
