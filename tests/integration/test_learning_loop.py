"""Integration: learning loop promote fixture and classifier."""

from __future__ import annotations

import json
from pathlib import Path

from context.model import ProjectContext
from learning.family_promotion import promote_family_to_library
from reasoning.classifier import classify_circuit_family
from utils.config import AppConfig

FIXTURE = (
    Path(__file__).resolve().parent.parent / "fixtures" / "bedini_aerf_live" / "stages_0-7.json"
)


def test_promote_bedini_fixture_and_reload_classifier(tmp_path: Path) -> None:
    lib = tmp_path / "kicad_ai_library"
    project = tmp_path / "bedini" / "Bedini.kicad_pro"
    project.parent.mkdir(parents=True)
    project.write_text("(stub)\n")

    stages = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ctx = ProjectContext(project_path=str(project), project_name="Bedini", symbols=[])
    cfg = AppConfig(
        artifact_library_path=lib,
        learning_auto_promote=True,
        learning_min_confidence="medium",
    )

    result = promote_family_to_library(stages, ctx, project, config=cfg)
    assert result.promoted
    assert result.family_id == "blocking_oscillator"

    classification = classify_circuit_family(ctx, config=cfg)
    assert classification.family_id in ("blocking_oscillator", "generic")
