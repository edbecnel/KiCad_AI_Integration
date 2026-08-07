"""AERF stage output schemas and validation (AERF Stage Index + ADP-007)."""

from __future__ import annotations

from typing import Any

CONFIDENCE_LEVELS: tuple[str, ...] = ("high", "medium", "low")

KNOWLEDGE_CLASSIFICATION_KEYS: tuple[str, ...] = (
    "measured_observation",
    "extracted_fact",
    "engineering_inference",
    "engineering_assumption",
    "engineering_hypothesis",
    "theoretical_framework",
    "project_design_intent",
    "mainstream_engineering_model",
    "simulation_result",
    "unknown",
)

# Required top-level keys in ``determinations`` per stage (AERF Stage Index).
STAGE_DETERMINATION_KEYS: dict[int, tuple[str, ...]] = {
    0: (
        "family_id",
        "family_label",
        "topology",
        "functional_blocks",
        "inputs",
        "outputs",
    ),
    1: (
        "operating_sequence",
        "startup_behavior",
        "control_mechanism",
    ),
    2: (
        "energy_source",
        "storage_elements",
        "transfer_path",
        "outputs",
    ),
    3: (
        "governing_equations",
    ),
    4: ("components",),
    5: ("modes",),
    6: (
        "mechanical_interactions",
        "thermal_effects",
        "environmental_influences",
        "external_systems",
    ),
    7: (
        "performance_evaluation",
        "failure_analysis",
        "optimization_suggestions",
        "measurement_recommendations",
        "design_improvements",
        "conclusions",
    ),
}

# JSON schema excerpts for prompts (determinations object per stage).
STAGE_DETERMINATIONS_SCHEMA_JSON: dict[int, str] = {
    0: """{
  "family_id": "string",
  "family_label": "string",
  "topology": "string",
  "functional_blocks": [{"name": "string", "description": "string"}],
  "inputs": [{"name": "string", "type": "string", "description": "string"}],
  "outputs": [{"name": "string", "type": "string", "description": "string"}],
  "switching_method": "string|null",
  "energy_storage_method": "string|null"
}""",
    1: """{
  "operating_sequence": ["string"],
  "startup_behavior": "string",
  "switching_mechanism": "string|null",
  "oscillation_cycle": "string|null",
  "control_mechanism": "string"
}""",
    2: """{
  "energy_source": "string",
  "storage_elements": [{"element": "string", "role": "string"}],
  "transfer_path": "string",
  "losses": [{"mechanism": "string", "location": "string", "estimate": "string|null"}],
  "outputs": [{"name": "string", "form": "string", "description": "string"}]
}""",
    3: """{
  "magnetic_behavior": "string|null",
  "electric_field_interactions": "string|null",
  "semiconductor_physics": "string|null",
  "governing_equations": [{"name": "string", "expression": "string", "applicability": "string"}]
}""",
    4: """{
  "components": [
    {
      "reference": "string",
      "value": "string",
      "purpose": "string",
      "interactions": ["string"],
      "design_intent": "string",
      "possible_substitutions": [{"part": "string", "tradeoffs": "string"}]
    }
  ]
}""",
    5: """{
  "modes": [
    {
      "mode": "startup|steady_state|fault|loading_change|component_failure|environmental",
      "description": "string",
      "behavior": "string",
      "risks": ["string"]
    }
  ]
}""",
    6: """{
  "mechanical_interactions": "string|null",
  "thermal_effects": "string|null",
  "environmental_influences": "string|null",
  "external_systems": [{"system": "string", "interaction": "string"}]
}""",
    7: """{
  "performance_evaluation": "string",
  "failure_analysis": [{"failure_mode": "string", "cause": "string", "mitigation": "string"}],
  "optimization_suggestions": [{"area": "string", "suggestion": "string", "tradeoffs": "string"}],
  "simulation_interpretation": "string|null",
  "measurement_recommendations": [{"measurement": "string", "instrument": "string", "expected_result": "string"}],
  "design_improvements": [{"improvement": "string", "rationale": "string"}],
  "conclusions": ["string"]
}""",
}

ENVELOPE_SCHEMA_JSON = """{
  "stage_id": 0,
  "stage_key": "circuit_identification",
  "title": "Circuit Identification",
  "question": "What is this circuit?",
  "determinations": {},
  "open_questions": [],
  "confidence": "high|medium|low",
  "unknowns": [],
  "simulation_hooks": [
    {"description": "string", "validates": "string", "expected_outcome": "string"}
  ],
  "sources": ["project_context", "circuit_family_kb", "prior_stages", "ekm"]
}"""

EVIDENCE_CHAIN_EXAMPLE_JSON = """{
  "statement": "string",
  "knowledge_classification": "extracted_fact|engineering_inference|...",
  "evidence": ["symbol R1 value from project_context", "net label HV_Flyback"],
  "confidence": "high|medium|low"
}"""


def validate_stage_envelope(
    payload: dict[str, Any],
    *,
    expected_stage_id: int | None = None,
    require_determination_keys: bool = True,
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate parsed AERF stage JSON beyond minimal envelope keys."""
    stage_id = payload.get("stage_id")
    if not isinstance(stage_id, int):
        return None, "stage_id must be an integer"

    if expected_stage_id is not None and stage_id != expected_stage_id:
        return None, f"stage_id {stage_id} does not match expected {expected_stage_id}"

    if not isinstance(payload.get("determinations"), dict):
        return None, "determinations must be an object"

    for key in ("open_questions", "unknowns"):
        if key in payload and not isinstance(payload[key], list):
            return None, f"{key} must be a list when present"

    if "simulation_hooks" in payload and not isinstance(payload["simulation_hooks"], list):
        return None, "simulation_hooks must be a list when present"

    confidence = payload.get("confidence")
    if confidence is not None:
        if not isinstance(confidence, str) or confidence not in CONFIDENCE_LEVELS:
            return None, f"confidence must be one of: {', '.join(CONFIDENCE_LEVELS)}"

    if require_determination_keys:
        required = STAGE_DETERMINATION_KEYS.get(stage_id)
        if required:
            determinations = payload["determinations"]
            missing = [k for k in required if k not in determinations]
            if missing:
                return None, (
                    f"determinations missing required keys for stage {stage_id}: "
                    f"{', '.join(missing)}"
                )

    return payload, None
