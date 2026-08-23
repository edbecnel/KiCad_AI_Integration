"""Translate AERF simulation hooks into plans and closed-loop refinements (ADP-006)."""

from __future__ import annotations

import re
from typing import Any

from inference.simulation_types import (
    SimulationHook,
    SimulationMeasurement,
    SimulationPlan,
    SimulationPlanStep,
    SimulationResult,
    StageRefinement,
)

_TRANSIENT_RE = re.compile(r"\b(transient|time.?domain|waveform|startup)\b", re.I)
_DC_RE = re.compile(r"\b(dc|steady.?state|quiescent)\b", re.I)
_AC_RE = re.compile(r"\b(ac|frequency|bode|impedance)\b", re.I)
_PARAM_RE = re.compile(r"\b(parametric|sweep|vary|adjust)\b", re.I)
_PROBE_RE = re.compile(r"\b(?:at|measure|monitor|voltage|current)\s+([A-Za-z0-9_./+-]+)", re.I)
_SUBCKT_RE = re.compile(r"\b(?:SUBCKT|spice model|realistic)\s+([A-Za-z0-9_-]+)", re.I)


def _infer_analysis_kind(description: str) -> str:
    if _PARAM_RE.search(description):
        return "parametric"
    if _TRANSIENT_RE.search(description):
        return "transient"
    if _AC_RE.search(description):
        return "ac"
    if _DC_RE.search(description):
        return "dc"
    return "unknown"


def _extract_probes(description: str) -> list[str]:
    probes: list[str] = []
    for match in _PROBE_RE.finditer(description):
        candidate = match.group(1).strip(".,;")
        if candidate and candidate not in probes:
            probes.append(candidate)
    return probes


def _extract_subckt_parts(description: str) -> list[str]:
    parts: list[str] = []
    for match in _SUBCKT_RE.finditer(description):
        part = match.group(1)
        if part and part not in parts:
            parts.append(part)
    return parts


def parse_simulation_hook(raw: dict[str, Any]) -> SimulationHook | None:
    description = raw.get("description")
    if not isinstance(description, str) or not description.strip():
        return None
    validates = raw.get("validates")
    expected = raw.get("expected_outcome")
    analysis_kind = raw.get("analysis_kind")
    probes_raw = raw.get("probes")
    probes = (
        [str(p) for p in probes_raw if isinstance(p, str)]
        if isinstance(probes_raw, list)
        else _extract_probes(description)
    )
    kind = analysis_kind if isinstance(analysis_kind, str) else _infer_analysis_kind(description)
    return SimulationHook(
        description=description.strip(),
        validates=str(validates) if isinstance(validates, str) else "",
        expected_outcome=str(expected) if isinstance(expected, str) else "",
        analysis_kind=kind,  # type: ignore[arg-type]
        probes=probes,
    )


def translate_simulation_hooks(
    stage_payload: dict[str, Any],
) -> SimulationPlan | None:
    """Translate AERF stage ``simulation_hooks`` into an executable plan."""
    hooks_raw = stage_payload.get("simulation_hooks")
    if not isinstance(hooks_raw, list) or not hooks_raw:
        return None
    stage_id = stage_payload.get("stage_id")
    stage_key = stage_payload.get("stage_key")
    hooks: list[SimulationHook] = []
    for item in hooks_raw:
        if not isinstance(item, dict):
            continue
        hook = parse_simulation_hook(item)
        if hook is not None:
            hooks.append(hook)
    if not hooks:
        return None
    steps: list[SimulationPlanStep] = []
    for hook in hooks:
        subckt_parts = _extract_subckt_parts(hook.description)
        notes: list[str] = []
        if hook.validates:
            notes.append(f"Validates: {hook.validates}")
        if hook.expected_outcome:
            notes.append(f"Expected: {hook.expected_outcome}")
        steps.append(
            SimulationPlanStep(
                hook=hook,
                netlist_required=True,
                subckt_parts=subckt_parts,
                notes=notes,
            )
        )
    return SimulationPlan(
        stage_id=int(stage_id) if isinstance(stage_id, int) else None,
        stage_key=str(stage_key) if isinstance(stage_key, str) else "",
        steps=steps,
        source_hooks=hooks,
    )


def build_refinement_from_simulation(
    stage_payload: dict[str, Any],
    result: SimulationResult,
    *,
    approved: bool = False,
) -> StageRefinement:
    """Map simulation measurements to stage refinement proposals."""
    stage_id = stage_payload.get("stage_id")
    stage_key = stage_payload.get("stage_key")
    determinations = stage_payload.get("determinations")
    validated: dict[str, Any] = {}
    challenged: dict[str, Any] = {}
    notes: list[str] = []
    if isinstance(determinations, dict):
        for step in result.plan.steps:
            if step.hook.validates:
                notes.append(f"Hook validates: {step.hook.validates}")
    for measurement in result.measurements:
        line = f"{measurement.name}: {measurement.value}"
        if measurement.unit:
            line += f" {measurement.unit}"
        if measurement.passed is True:
            validated[measurement.name] = line
        elif measurement.passed is False:
            challenged[measurement.name] = line
        else:
            notes.append(line)
    if result.success:
        notes.append("Simulation completed successfully.")
    else:
        notes.extend(result.errors or ["Simulation did not complete successfully."])
    return StageRefinement(
        stage_id=int(stage_id) if isinstance(stage_id, int) else -1,
        stage_key=str(stage_key) if isinstance(stage_key, str) else "",
        validated_determinations=validated,
        challenged_determinations=challenged,
        refinement_notes=notes,
        approved=approved,
    )


def merge_refinement_into_stage(
    stage_payload: dict[str, Any],
    refinement: StageRefinement,
) -> dict[str, Any]:
    """Return a copy of stage payload with approved refinement merged."""
    if not refinement.approved:
        raise ValueError("Refinement must be approved before merging into stage payload.")
    merged = dict(stage_payload)
    determinations = dict(merged.get("determinations") or {})
    sim_validation = dict(determinations.get("simulation_validation") or {})
    sim_validation["validated"] = refinement.validated_determinations
    sim_validation["challenged"] = refinement.challenged_determinations
    sim_validation["notes"] = refinement.refinement_notes
    determinations["simulation_validation"] = sim_validation
    merged["determinations"] = determinations
    return merged
