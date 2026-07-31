"""Tests for AERF → EKM write-back mapping."""

from __future__ import annotations

import json
from pathlib import Path

from ekm import EKMDocument, load, plan_aerf_writeback, write_aerf_stages_to_ekm
from ekm.aerf_writeback import apply_aerf_writeback
from ekm.validate import validate_document_data


def _stage(stage_id: int, **determinations: object) -> dict:
    return {
        "stage_id": stage_id,
        "determinations": determinations,
        "open_questions": [],
        "unknowns": [],
        "confidence": "high",
    }


def _fixture_stages() -> list[dict]:
    return [
        _stage(0, family_id="blocking_oscillator", topology="flyback"),
        _stage(1, principle="regenerative feedback"),
        _stage(2, energy_path="transformer primary"),
        _stage(3, behavior="self-oscillating"),
        _stage(4, components={"Q1": "switch"}),
        _stage(5, conditions={"supply": "12V"}),
        _stage(6, system_behavior="pulsed output"),
        {
            "stage_id": 7,
            "determinations": {
                "conclusions": "Design is plausible for low-power use.",
                "recommendations": ["Measure peak collector current"],
                "risks": ["Core saturation at high duty"],
            },
            "open_questions": ["What is measured switching frequency?"],
            "unknowns": [],
            "confidence": "medium",
        },
        {
            "stage_id": 0,
            "determinations": {},
            "open_questions": ["Is phasing verified?"],
            "unknowns": [],
            "confidence": "low",
        },
    ]


def test_plan_aerf_writeback_section_ids() -> None:
    plan = plan_aerf_writeback(_fixture_stages()[:8])
    assert "circuit_overview" in plan.section_ids
    assert "operation_and_principles" in plan.section_ids
    assert "component_rationale" in plan.section_ids
    assert "operating_conditions" in plan.section_ids
    assert "analysis" in plan.section_ids
    assert "recommendations" in plan.section_ids
    assert plan.has_stage_7 is True
    assert plan.stage_count == 8


def test_apply_aerf_writeback_validates() -> None:
    doc = EKMDocument.empty()
    apply_aerf_writeback(doc, _fixture_stages()[:8])
    validate_document_data(doc.to_dict())
    section_ids = {section["id"] for section in doc.sections}
    assert "analysis" in section_ids
    analysis = next(s for s in doc.sections if s["id"] == "analysis")
    assert any(f["id"] == "aerf_stage_7_analysis" for f in analysis["fields"])


def test_open_questions_map_to_open_items() -> None:
    doc = EKMDocument.empty()
    apply_aerf_writeback(doc, _fixture_stages())
    open_items = next(s for s in doc.sections if s["id"] == "open_items")
    enum_fields = [f for f in open_items["fields"] if f["type"] == "enum"]
    assert len(enum_fields) >= 2
    assert enum_fields[0]["value"] == "Pending Review"


def test_write_without_approve_does_not_create_file(tmp_path: Path) -> None:
    stages = _fixture_stages()[:1]
    plan, saved = write_aerf_stages_to_ekm(tmp_path, stages, approve=False)
    assert plan.stage_count == 1
    assert saved is None
    assert not (tmp_path / "kicad_ai" / "engineering_knowledge.json").exists()


def test_write_with_approve_round_trip(tmp_path: Path) -> None:
    stages = _fixture_stages()[:8]
    plan, saved = write_aerf_stages_to_ekm(tmp_path, stages, approve=True)
    assert saved is not None
    assert saved.is_file()
    doc = load(saved)
    assert plan.has_stage_7
    data = json.loads(saved.read_text(encoding="utf-8"))
    validate_document_data(data)
    assert doc.updated_at is not None
