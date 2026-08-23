"""Tests for PI/SI/EMC and flyback audit prompt templates."""

from __future__ import annotations

from context.collector import collect_stretch_context
from prompts.builder import (
    build_emi_emc_prompt,
    build_flyback_recovery_prompt,
    build_power_integrity_prompt,
    build_signal_integrity_prompt,
)


def test_domain_audit_prompts(blocking_oscillator_pro) -> None:
    ctx = collect_stretch_context(blocking_oscillator_pro)
    for builder in (
        build_power_integrity_prompt,
        build_signal_integrity_prompt,
        build_emi_emc_prompt,
        build_flyback_recovery_prompt,
    ):
        built = builder(ctx, "Review this design.")
        assert built.text
        assert built.system
        assert built.estimated_text_tokens > 0
