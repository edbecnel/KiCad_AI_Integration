"""Tests for inference simulation re-exports and AERF stub."""

from __future__ import annotations

from context.model import ProjectContext
from context.schematic_parse import SymbolInstance
from inference.aerf import (
    build_aerf_stage_prompt_bundle,
    build_stage0_bundle,
    classify_and_plan,
)
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


def test_aerf_stage0_auto_classify() -> None:
    ctx = ProjectContext(
        project_path="/tmp/p",
        project_name="demo",
        symbols=[
            SymbolInstance(reference="Q1", value="2N3055", lib_id="Device:Q_NPN_BCE"),
            SymbolInstance(reference="T1", value="Coil", lib_id="Device:T_Core"),
        ],
        schematic_connectivity={"unique_net_names": ["Trigger", "Coil_Plus"]},
    )
    bundle = build_stage0_bundle(ctx, preview_chars=200)
    assert bundle.family_id == "blocking_oscillator"
    assert bundle.classification is not None
    assert bundle.classification.confidence in ("medium", "high")


def test_classify_and_plan() -> None:
    ctx = ProjectContext(project_path="/tmp/p", project_name="demo")
    classification, plan = classify_and_plan(ctx, user_hint="blocking oscillator")
    assert classification.family_id == "blocking_oscillator"
    assert plan.stage.stage_id == 0


def test_aerf_stage_prompt_bundle_dry_run() -> None:
    ctx = ProjectContext(project_path="/tmp/p", project_name="demo")
    plan, built = build_aerf_stage_prompt_bundle(ctx, "blocking_oscillator", 1)
    assert plan.stage.stage_id == 1
    assert built.template == "aerf_stage_1"
    assert "<circuit_family_kb>" in built.text
