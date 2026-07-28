"""Tests for SUBCKT prompt templates."""

from __future__ import annotations

from prompts.templates.subckt import (
    build_subckt_facts_prompt,
    build_subckt_prompt_for_tier,
    build_subckt_synthesis_prompt,
    build_subckt_tier_b_prompt,
)


def test_build_subckt_facts_prompt_includes_pdf_text() -> None:
    sym = {"reference": "U3", "value": "F0D3180", "lib_id": "Opto:FOD3180"}
    user, system = build_subckt_facts_prompt(
        "F0D3180",
        sym,
        datasheet_text="Pin 1 is anode",
        pdf_path="/tmp/F0D3180.pdf",
    )
    assert "F0D3180" in user
    assert "Pin 1 is anode" in user
    assert "JSON" in system


def test_build_subckt_synthesis_prompt_includes_facts() -> None:
    sym = {"reference": "U3", "value": "F0D3180"}
    facts = {"part": "F0D3180", "pinout": []}
    user, system = build_subckt_synthesis_prompt("F0D3180", sym, facts)
    assert "pinout" in user
    assert ".SUBCKT" in system


def test_build_subckt_tier_b_prompt() -> None:
    sym = {"reference": "U3", "value": "F0D3180"}
    user, system = build_subckt_tier_b_prompt("F0D3180", sym)
    assert "No datasheet PDF" in user
    assert "behavioral" in system.lower()


def test_build_subckt_prompt_for_tier_c() -> None:
    sym = {"reference": "U3", "value": "F0D3180"}
    user, system = build_subckt_prompt_for_tier("C", "F0D3180", sym)
    assert "last-resort" in user.lower() or "Last-resort" in user
