"""Tests for EKM prompt context (learning loop L1)."""

from __future__ import annotations

import json
from pathlib import Path

from ekm import write_aerf_stages_to_ekm
from ekm.prompt_context import (
    extract_ekm_family_id,
    load_ekm_prompt_bundle,
    load_ekm_sections_for_prompt,
)
from inference.aerf import build_aerf_stage_prompt_bundle, run_aerf_pipeline
from context.model import ProjectContext


def _stage(stage_id: int, family_id: str = "buck_converter") -> dict:
    keys = {
        0: {
            "family_id": family_id,
            "family_label": "Buck",
            "topology": "buck",
            "functional_blocks": [],
            "inputs": [],
            "outputs": [],
        },
    }
    det = keys.get(stage_id, {"note": "ok"})
    return {
        "stage_id": stage_id,
        "stage_key": "test",
        "determinations": det,
        "open_questions": [],
        "unknowns": [],
        "confidence": "high",
    }


def test_writeback_and_reload_family_id(tmp_path: Path) -> None:
    project = tmp_path / "demo.kicad_pro"
    project.write_text("(kicad_pro stub)\n")
    stages = [_stage(0)]
    write_aerf_stages_to_ekm(tmp_path, stages, approve=True)

    bundle = load_ekm_prompt_bundle(project)
    assert bundle.family_id == "buck_converter"
    assert "circuit_overview" in bundle.sections


def test_ekm_sections_in_aerf_prompt(tmp_path: Path) -> None:
    project = tmp_path / "demo.kicad_pro"
    project.write_text("(kicad_pro stub)\n")
    write_aerf_stages_to_ekm(tmp_path, [_stage(0, "blocking_oscillator")], approve=True)

    ctx = ProjectContext(project_path=str(project), project_name="demo")
    bundle = load_ekm_prompt_bundle(project)
    _plan, built = build_aerf_stage_prompt_bundle(
        ctx,
        "blocking_oscillator",
        0,
        ekm_sections=bundle.sections,
    )
    assert "circuit_overview" in built.text


def test_pipeline_auto_loads_ekm(tmp_path: Path) -> None:
    project = tmp_path / "demo.kicad_pro"
    project.write_text("(kicad_pro stub)\n")
    write_aerf_stages_to_ekm(tmp_path, [_stage(0, "blocking_oscillator")], approve=True)

    ctx = ProjectContext(project_path=str(project), project_name="demo")
    result = run_aerf_pipeline(ctx, approve_send=False)
    assert result.family_id == "blocking_oscillator"
