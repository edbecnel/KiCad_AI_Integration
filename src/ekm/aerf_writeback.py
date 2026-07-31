"""Map approved AERF stage envelopes to EKM sections (ADP-008 §15, Track C4)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ekm.io import load, save
from ekm.model import EKMDocument
from ekm.paths import resolve_ekm_path

_OPEN_QUESTION_STATUS = "Pending Review"
_OPEN_QUESTION_OPTIONS = ["Pending Review", "Resolved", "Deferred"]

_SECTION_SPECS: dict[str, dict[str, Any]] = {
    "circuit_overview": {"title": "Circuit Overview", "order": 0},
    "operation_and_principles": {"title": "Operation and Principles", "order": 1},
    "component_rationale": {"title": "Component Rationale", "order": 2},
    "operating_conditions": {"title": "Operating Conditions", "order": 3},
    "analysis": {"title": "Analysis", "order": 4},
    "recommendations": {"title": "Recommendations", "order": 5},
    "open_items": {"title": "Open Items", "order": 6},
}


@dataclass
class AERFWritebackFieldPlan:
    """One EKM field create/update in a write-back plan."""

    section_id: str
    field_id: str
    action: str
    label: str
    field_type: str
    value_preview: str


@dataclass
class AERFWritebackPlan:
    """Dry-run summary of EKM mutations from AERF stage outputs."""

    section_ids: list[str] = field(default_factory=list)
    field_plans: list[AERFWritebackFieldPlan] = field(default_factory=list)
    stage_count: int = 0
    has_stage_7: bool = False
    summary: str = ""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _preview(value: str, *, limit: int = 120) -> str:
    text = value.replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _json_text(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _index_stages(stage_outputs: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    indexed: dict[int, dict[str, Any]] = {}
    for envelope in stage_outputs:
        stage_id = envelope.get("stage_id")
        if isinstance(stage_id, int):
            indexed[stage_id] = envelope
    return indexed


def _text_field(
    field_id: str,
    *,
    label: str,
    value: str,
    source: str,
    approved_at: str,
) -> dict[str, Any]:
    return {
        "id": field_id,
        "type": "text",
        "label": label,
        "value": value,
        "metadata": {
            "source": source,
            "approved_at": approved_at,
        },
    }


def _open_question_field(
    stage_id: int,
    index: int,
    question: str,
    *,
    approved_at: str,
) -> dict[str, Any]:
    return {
        "id": f"open_question_stage_{stage_id}_{index}",
        "type": "enum",
        "label": f"Open question (stage {stage_id})",
        "value": _OPEN_QUESTION_STATUS,
        "options": list(_OPEN_QUESTION_OPTIONS),
        "metadata": {
            "source": f"aerf_stage_{stage_id}",
            "question": question,
            "status": _OPEN_QUESTION_STATUS,
            "approved_at": approved_at,
        },
    }


def _stage7_text_parts(determinations: dict[str, Any]) -> tuple[str, str]:
    analysis_keys = ("conclusions", "analysis", "risks", "confidence_summary")
    recommendation_keys = ("recommendations", "recommended_tests", "improvements")

    analysis_payload = {
        key: determinations[key] for key in analysis_keys if key in determinations
    }
    recommendation_payload = {
        key: determinations[key] for key in recommendation_keys if key in determinations
    }

    remaining = {
        key: value
        for key, value in determinations.items()
        if key not in analysis_keys and key not in recommendation_keys
    }
    if remaining:
        analysis_payload.setdefault("other", remaining)

    analysis_text = _json_text(analysis_payload) if analysis_payload else _json_text(determinations)
    recommendations_text = _json_text(recommendation_payload) if recommendation_payload else ""
    return analysis_text, recommendations_text


def _collect_field_specs(
    stages: dict[int, dict[str, Any]],
    *,
    approved_at: str,
) -> list[tuple[str, dict[str, Any]]]:
    """Return (section_id, field_dict) pairs to upsert."""
    specs: list[tuple[str, dict[str, Any]]] = []

    if 0 in stages:
        value = _json_text(stages[0].get("determinations", {}))
        specs.append(
            (
                "circuit_overview",
                _text_field(
                    "aerf_stage_0_determinations",
                    label="AERF stage 0 — circuit identification",
                    value=value,
                    source="aerf_stage_0",
                    approved_at=approved_at,
                ),
            )
        )

    stages_1_3 = {sid: stages[sid] for sid in (1, 2, 3) if sid in stages}
    if stages_1_3:
        payload = {
            str(sid): stages_1_3[sid].get("determinations", {})
            for sid in sorted(stages_1_3)
        }
        specs.append(
            (
                "operation_and_principles",
                _text_field(
                    "aerf_stages_1_3_determinations",
                    label="AERF stages 1–3 — operation and principles",
                    value=_json_text(payload),
                    source="aerf_stages_1_3",
                    approved_at=approved_at,
                ),
            )
        )

    if 4 in stages:
        specs.append(
            (
                "component_rationale",
                _text_field(
                    "aerf_stage_4_determinations",
                    label="AERF stage 4 — component rationale",
                    value=_json_text(stages[4].get("determinations", {})),
                    source="aerf_stage_4",
                    approved_at=approved_at,
                ),
            )
        )

    stages_5_6 = {sid: stages[sid] for sid in (5, 6) if sid in stages}
    if stages_5_6:
        payload = {
            str(sid): stages_5_6[sid].get("determinations", {})
            for sid in sorted(stages_5_6)
        }
        specs.append(
            (
                "operating_conditions",
                _text_field(
                    "aerf_stages_5_6_determinations",
                    label="AERF stages 5–6 — operating conditions",
                    value=_json_text(payload),
                    source="aerf_stages_5_6",
                    approved_at=approved_at,
                ),
            )
        )

    if 7 in stages:
        determinations = stages[7].get("determinations", {})
        if not isinstance(determinations, dict):
            determinations = {}
        analysis_text, recommendations_text = _stage7_text_parts(determinations)
        specs.append(
            (
                "analysis",
                _text_field(
                    "aerf_stage_7_analysis",
                    label="AERF stage 7 — engineering analysis",
                    value=analysis_text,
                    source="aerf_stage_7",
                    approved_at=approved_at,
                ),
            )
        )
        if recommendations_text:
            specs.append(
                (
                    "recommendations",
                    _text_field(
                        "aerf_stage_7_recommendations",
                        label="AERF stage 7 — recommendations",
                        value=recommendations_text,
                        source="aerf_stage_7",
                        approved_at=approved_at,
                    ),
                ),
            )

    for stage_id in sorted(stages):
        open_questions = stages[stage_id].get("open_questions") or []
        if not isinstance(open_questions, list):
            continue
        for index, question in enumerate(open_questions):
            if not isinstance(question, str) or not question.strip():
                continue
            specs.append(
                (
                    "open_items",
                    _open_question_field(
                        stage_id,
                        index,
                        question.strip(),
                        approved_at=approved_at,
                    ),
                ),
            )

    return specs


def plan_aerf_writeback(
    stage_outputs: list[dict[str, Any]],
    *,
    approved_at: str | None = None,
) -> AERFWritebackPlan:
    """Build a dry-run plan from parsed AERF stage envelopes."""
    stages = _index_stages(stage_outputs)
    timestamp = approved_at or _utc_now_iso()
    field_specs = _collect_field_specs(stages, approved_at=timestamp)

    section_ids: list[str] = []
    field_plans: list[AERFWritebackFieldPlan] = []
    for section_id, fld in field_specs:
        if section_id not in section_ids:
            section_ids.append(section_id)
        field_plans.append(
            AERFWritebackFieldPlan(
                section_id=section_id,
                field_id=str(fld["id"]),
                action="upsert",
                label=str(fld.get("label") or fld["id"]),
                field_type=str(fld["type"]),
                value_preview=_preview(
                    fld["value"] if fld["type"] == "text" else str(fld.get("metadata", {}).get("question", ""))
                ),
            )
        )

    open_count = sum(1 for fp in field_plans if fp.section_id == "open_items")
    det_count = len(field_plans) - open_count
    summary = (
        f"Upsert {len(section_ids)} EKM section(s), {det_count} determination field(s)"
        + (f", {open_count} open question(s)" if open_count else "")
        + f" from {len(stages)} stage envelope(s)."
    )
    return AERFWritebackPlan(
        section_ids=section_ids,
        field_plans=field_plans,
        stage_count=len(stages),
        has_stage_7=7 in stages,
        summary=summary,
    )


def _upsert_field(section: dict[str, Any], field: dict[str, Any]) -> str:
    fields = section.setdefault("fields", [])
    field_id = field["id"]
    for index, existing in enumerate(fields):
        if isinstance(existing, dict) and existing.get("id") == field_id:
            fields[index] = field
            return "update"
    fields.append(field)
    return "create"


def _ensure_section(doc: EKMDocument, section_id: str) -> dict[str, Any]:
    for section in doc.sections:
        if section.get("id") == section_id:
            return section

    spec = _SECTION_SPECS[section_id]
    section = {
        "id": section_id,
        "title": spec["title"],
        "order": spec["order"],
        "fields": [],
    }
    doc.sections.append(section)
    doc.sections.sort(key=lambda s: int(s.get("order", 0)))
    return section


def apply_aerf_writeback(
    doc: EKMDocument,
    stage_outputs: list[dict[str, Any]],
    *,
    approved_at: str | None = None,
) -> EKMDocument:
    """Merge approved AERF stage outputs into an EKM document (in memory)."""
    timestamp = approved_at or _utc_now_iso()
    field_specs = _collect_field_specs(_index_stages(stage_outputs), approved_at=timestamp)

    for section_id, fld in field_specs:
        section = _ensure_section(doc, section_id)
        _upsert_field(section, fld)

    return doc


def write_aerf_stages_to_ekm(
    project_path: Path | str,
    stage_outputs: list[dict[str, Any]],
    *,
    approve: bool = False,
    approved_at: str | None = None,
) -> tuple[AERFWritebackPlan, Path | None]:
    """Plan EKM write-back; persist only when ``approve`` is True."""
    path = Path(project_path).expanduser()
    ekm_path = resolve_ekm_path(path)
    if ekm_path.is_file():
        doc = load(path)
    else:
        project_dir = ekm_path.parent.parent
        project_ref = str(path) if path.suffix == ".kicad_pro" else str(project_dir)
        doc = EKMDocument.empty(project_path=project_ref)

    timestamp = approved_at or _utc_now_iso()
    plan = plan_aerf_writeback(stage_outputs, approved_at=timestamp)
    apply_aerf_writeback(doc, stage_outputs, approved_at=timestamp)

    if not approve:
        return plan, None

    saved = save(doc, path)
    return plan, saved
