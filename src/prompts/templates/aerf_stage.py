"""AERF per-stage prompt template (ADP-007)."""

from __future__ import annotations

import json
from typing import Any

from platform_core.contracts import DesignSnapshot
from prompts.compact import compact_snapshot_for_prompt
from reasoning import get_stage, load_stage_excerpt
from reasoning.stage_schemas import (
    EVIDENCE_CHAIN_EXAMPLE_JSON,
    ENVELOPE_SCHEMA_JSON,
    KNOWLEDGE_CLASSIFICATION_KEYS,
    STAGE_DETERMINATIONS_SCHEMA_JSON,
)
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

_CLASSIFICATION_LIST = ", ".join(KNOWLEDGE_CLASSIFICATION_KEYS)

AERF_METHODOLOGY_EXCERPT = f"""\
Follow the Engineering Reasoning Methodology for this stage:

1. Evidence collection — use project_context, circuit_family_kb, prior_stages, engineering_knowledge, user hints.
2. Observation classification — assign knowledge_classification to significant statements using keys:
   {_CLASSIFICATION_LIST}
3. Hypothesis generation — form hypotheses supported by evidence; note competing explanations.
4. Topology recognition, component roles, energy/signal path tracing as applicable to this stage.
5. Confidence estimation — overall stage confidence: high, medium, or low.
6. Unknown identification — list gaps in unknowns; do not fabricate data to fill them.
7. Contradictory evidence — surface conflicts; lower confidence or add open_questions when unresolved.
8. Integrity principle — never present assumptions, hypotheses, theoretical_framework, or
   project_design_intent as established engineering knowledge without classification.
9. Scientific neutrality — respect project_design_intent; do not dismiss unconventional designs;
   classify theoretical_framework separately from mainstream_engineering_model when they differ.
10. Traceable conclusions — cite evidence briefly in strings; use open_questions/unknowns for gaps.
"""

AERF_OUTPUT_DISCIPLINE = """\
CRITICAL output rules:
- Return ONE complete, valid JSON object matching aerf_output_schema (envelope + determinations for this stage).
- determinations MUST contain ONLY the keys listed in aerf_output_schema for this stage — no extra keys.
- Use concise strings (1–3 sentences). Limit arrays to 6 items unless the schema requires more.
- Do NOT add nested evidence-chain objects inside determinations unless the schema explicitly shows that shape.
- Use family_id "blocking_oscillator" when the circuit matches the Blocking Oscillator / Bedini SSG family.
- Ensure JSON is complete and parseable — never truncate mid-object.
"""

AERF_STAGE_SYSTEM = (
    "You are an expert electronics design engineer performing staged AERF circuit analysis. "
    "Answer the stage question using the structured context below. "
    "Return a single JSON object matching aerf_output_schema (envelope + determinations for this stage). "
    "Required envelope keys: stage_id, stage_key, determinations, open_questions, unknowns, confidence. "
    "Optional: simulation_hooks, sources. "
    "Follow aerf_output_discipline — concise schema-only JSON."
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

    determinations_schema = STAGE_DETERMINATIONS_SCHEMA_JSON.get(stage_id, "{}")

    sections: dict[str, str] = {}
    sections["aerf_stage"] = json.dumps(_stage_metadata(stage), indent=2)
    sections["aerf_prior_stages"] = json.dumps(prior_stages or [], indent=2)
    sections["circuit_family_kb"] = excerpt.content
    sections["kicad_python_extracted_data"] = json.dumps(context_data, indent=2)
    sections["engineering_knowledge"] = json.dumps(ekm_sections or {}, indent=2)
    sections["aerf_methodology"] = AERF_METHODOLOGY_EXCERPT.strip()
    sections["aerf_output_discipline"] = AERF_OUTPUT_DISCIPLINE.strip()
    sections["aerf_evidence_model"] = EVIDENCE_CHAIN_EXAMPLE_JSON.strip()
    sections["aerf_output_schema"] = (
        f"Envelope shape:\n{ENVELOPE_SCHEMA_JSON.strip()}\n\n"
        f"determinations schema for stage {stage_id}:\n{determinations_schema.strip()}"
    )
    return sections


def aerf_stage_system_message(stage_id: int) -> str:
    """System role for a specific AERF stage."""
    stage = get_stage(stage_id)
    question = STAGE_QUESTIONS[stage.stage_id]
    return f"{AERF_STAGE_SYSTEM} Stage {stage.stage_id} — {stage.title}: {question}"
