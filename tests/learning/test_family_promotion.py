"""Tests for circuit family library merge and promotion."""

from __future__ import annotations

import json
from pathlib import Path

from context.model import ProjectContext
from learning.family_promotion import check_promotion_gates, promote_family_to_library
from reasoning.family_registry import load_families
from reasoning.classifier import classify_circuit_family


def _full_stages(family_id: str = "buck_converter") -> list[dict]:
    stages = []
    for stage_id in range(8):
        det: dict = {"note": f"stage_{stage_id}"}
        if stage_id == 0:
            det = {
                "family_id": family_id,
                "family_label": "Buck Converter",
                "topology": "buck",
                "functional_blocks": [],
                "inputs": [],
                "outputs": [],
            }
        elif stage_id == 4:
            det = {"components": []}
        elif stage_id == 5:
            det = {"modes": []}
        elif stage_id == 3:
            det = {"governing_equations": []}
        elif stage_id == 7:
            det = {
                "performance_evaluation": "ok",
                "failure_analysis": [],
                "optimization_suggestions": [],
                "measurement_recommendations": [],
                "design_improvements": [],
                "conclusions": ["test"],
            }
        elif stage_id == 1:
            det = {
                "operating_sequence": [],
                "startup_behavior": "unknown",
                "control_mechanism": "pwm",
            }
        elif stage_id == 2:
            det = {
                "energy_source": "dc",
                "storage_elements": [],
                "transfer_path": "switch",
                "outputs": [],
            }
        elif stage_id == 6:
            det = {
                "mechanical_interactions": None,
                "thermal_effects": None,
                "environmental_influences": None,
                "external_systems": [],
            }
        stages.append(
            {
                "stage_id": stage_id,
                "stage_key": "test",
                "determinations": det,
                "open_questions": [],
                "unknowns": [],
                "confidence": "high",
            }
        )
    return stages


def test_library_manifest_merge(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    cf = lib / "circuit_families"
    cf.mkdir(parents=True)
    (cf / "families.json").write_text(
        json.dumps(
            {
                "families": [
                    {
                        "family_id": "learned_buck",
                        "directory": "Learned_Buck",
                        "label": "Learned Buck",
                        "status": "learned",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    families = load_families(library_path=lib)
    ids = {f.family_id for f in families}
    assert "blocking_oscillator" in ids
    assert "learned_buck" in ids


def test_promotion_writes_library(tmp_path: Path) -> None:
    from utils.config import AppConfig

    lib = tmp_path / "library"
    project = tmp_path / "proj" / "demo.kicad_pro"
    project.parent.mkdir(parents=True)
    project.write_text("(stub)\n")

    ctx = ProjectContext(project_path=str(project), project_name="demo")
    stages = _full_stages("buck_converter")
    cfg = AppConfig(artifact_library_path=lib, learning_auto_promote=True)

    ok, reason = check_promotion_gates(stages, min_confidence="high")
    assert ok, reason

    result = promote_family_to_library(stages, ctx, project, config=cfg)
    assert result.promoted
    assert result.family_id == "buck_converter"

    manifest = json.loads(
        (lib / "circuit_families" / "families.json").read_text(encoding="utf-8")
    )
    assert any(f["family_id"] == "buck_converter" for f in manifest["families"])
    assert (lib / "circuit_families" / "Buck_Converter" / "00 - Circuit Identification.md").is_file()


def test_generic_family_fallback() -> None:
    ctx = ProjectContext(project_path="/tmp/unknown.kicad_pro", project_name="unknown")
    classification = classify_circuit_family(ctx)
    assert classification.family_id in ("generic", "blocking_oscillator")
