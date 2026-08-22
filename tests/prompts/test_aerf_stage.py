"""Tests for AERF per-stage prompt templates."""

from __future__ import annotations

import json

import pytest

from context.model import ProjectContext
from prompts import build_aerf_stage_prompt
from reasoning import AERF_STAGE_COUNT


@pytest.mark.parametrize("stage_id", range(AERF_STAGE_COUNT))
def test_aerf_stage_prompt_xml_sections(stage_id: int) -> None:
    ctx = ProjectContext(project_path="/tmp/p", project_name="demo")
    built = build_aerf_stage_prompt(ctx, "blocking_oscillator", stage_id)
    assert built.template == f"aerf_stage_{stage_id}"
    assert built.system
    for tag in (
        "aerf_stage",
        "aerf_prior_stages",
        "circuit_family_kb",
        "kicad_python_extracted_data",
        "engineering_knowledge",
        "aerf_methodology",
        "aerf_output_discipline",
        "aerf_evidence_model",
        "aerf_output_schema",
    ):
        assert f"<{tag}>" in built.text
        assert f"</{tag}>" in built.text


def test_aerf_stage_prompt_kb_excerpt_present() -> None:
    ctx = ProjectContext(project_path="/tmp/p", project_name="demo")
    built = build_aerf_stage_prompt(ctx, "blocking_oscillator", 0)
    assert "Circuit Identification" in built.text


def test_aerf_stage_prompt_prior_stages_injected() -> None:
    ctx = ProjectContext(project_path="/tmp/p", project_name="demo")
    prior = [{"stage_id": 0, "determinations": {"family_id": "blocking_oscillator"}}]
    built = build_aerf_stage_prompt(
        ctx,
        "blocking_oscillator",
        2,
        prior_stages=prior,
    )
    assert '"stage_id": 0' in built.text
    prior_section = built.text.split("<aerf_prior_stages>")[1].split("</aerf_prior_stages>")[0]
    loaded = json.loads(prior_section.strip())
    assert loaded == prior
