"""AERF per-stage prompt template (ADP-007)."""

from __future__ import annotations

import json
from typing import Any

from platform_core.contracts import DesignSnapshot
from prompts.compact import compact_snapshot_for_prompt
from reasoning import get_stage, load_stage_excerpt
from reasoning.stages import AERFStage

STAGE_QUESTIONS: dict[int, str] = {
    0: "What is this circuit?",
    1: "How does it work?",
    2: "Where does the energy go?",
    3: "Why does it behave this way?",
    4: "What does every component contribute?",
    5: "How does behavior change?",
    6: "How does the complete system behave?",
    7: "What conclusions can an experienced engineer draw?",
}

AERF_METHODOLOGY_EXCERPT = """\
Follow the Engineering Reasoning Methodology for this stage:
1. Classify observations (measured, extracted, inferred, assumed, theoretical).
2. Generate hypotheses supported by evidence; note competing explanations.
3. Trace topology, component roles, and energy/signal paths as applicable.
4. Estimate confidence (high, medium, low) and flag unknowns explicitly.
5. Produce determinations with traceable evidence chains — never present assumptions as established fact.
"""

AERF_STAGE_SYSTEM = (
    "You are an expert electronics design engineer performing staged AERF circuit analysis. "
    "Answer the stage question using the structured context below. "
    "Return JSON with keys: stage_id, stage_key, determinations, open_questions, unknowns, confidence. "
    "Significant determinations must include knowledge classification and evidence chains."
)


def _stage_metadata(stage: AERFStage) -> dict[str, Any]:
    return {
        "stage_id": stage.stage_id,
        "stage_key": stage.stage_key,
        "title": stage.title,
        "question": STAGE_QUESTIONS[stage.stage_id],
    }


def build_aerf_stage_sections(
    snapshot: DesignSnapshot,
    family_id: str,
    stage_id: int,
    *,
    prior_stages: list[dict[str, Any]] | None = None,
    ekm_sections: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Return XML section name → body for an AERF stage prompt."""
    stage = get_stage(stage_id)
    excerpt = load_stage_excerpt(family_id, stage_id)
    context_data = compact_snapshot_for_prompt(snapshot)

    sections: dict[str, str] = {}
    sections["aerf_stage"] = json.dumps(_stage_metadata(stage), indent=2)
    sections["aerf_prior_stages"] = json.dumps(prior_stages or [], indent=2)
    sections["circuit_family_kb"] = excerpt.content
    sections["kicad_python_extracted_data"] = json.dumps(context_data, indent=2)
    sections["engineering_knowledge"] = json.dumps(ekm_sections or {}, indent=2)
    sections["aerf_methodology"] = AERF_METHODOLOGY_EXCERPT.strip()
    return sections


def aerf_stage_system_message(stage_id: int) -> str:
    """System role for a specific AERF stage."""
    stage = get_stage(stage_id)
    question = STAGE_QUESTIONS[stage.stage_id]
    return f"{AERF_STAGE_SYSTEM} Stage {stage.stage_id} — {stage.title}: {question}"
