"""Tests for inference simulation re-exports and AERF stub."""

from __future__ import annotations

from context.model import ProjectContext
from inference.aerf import build_stage0_bundle
from ui.simulation_supply import GAP_LABELS, get_simulation_panel_context


def test_simulation_supply_reexports() -> None:
    from inference.simulation import get_simulation_panel_context as infer_get

    assert get_simulation_panel_context is infer_get
    assert "missing_spice_model" in GAP_LABELS


def test_aerf_stage0_dry_run() -> None:
    ctx = ProjectContext(project_path="/tmp/p", project_name="demo")
    bundle = build_stage0_bundle(ctx, "blocking_oscillator", preview_chars=200)
    assert bundle.family_id == "blocking_oscillator"
    assert bundle.stage_plan.stage.stage_id == 0
    assert "Circuit Identification" in bundle.kb_excerpt_preview or len(bundle.kb_excerpt_preview) > 0
