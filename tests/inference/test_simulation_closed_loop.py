"""Tests for simulation closed-loop translation (ADP-006)."""

from __future__ import annotations

from inference.simulation_closed_loop import (
    build_refinement_from_simulation,
    merge_refinement_into_stage,
    translate_simulation_hooks,
)
from inference.simulation_types import (
    SimulationHook,
    SimulationMeasurement,
    SimulationPlan,
    SimulationPlanStep,
    SimulationResult,
)


def test_translate_simulation_hooks_from_stage_payload() -> None:
    payload = {
        "stage_id": 2,
        "stage_key": "energy_flow",
        "simulation_hooks": [
            {
                "description": "Transient simulation measuring current through Q1 collector",
                "validates": "Switching mechanism",
                "expected_outcome": "Sawtooth waveform",
            }
        ],
    }
    plan = translate_simulation_hooks(payload)
    assert plan is not None
    assert plan.stage_id == 2
    assert plan.stage_key == "energy_flow"
    assert len(plan.steps) == 1
    assert plan.steps[0].hook.analysis_kind == "transient"
    assert plan.steps[0].netlist_required is True


def test_build_refinement_from_simulation() -> None:
    hook = SimulationHook(description="Measure frequency", validates="Oscillation")
    plan = SimulationPlan(stage_id=1, stage_key="basic_oscillation", steps=[SimulationPlanStep(hook=hook)])
    result = SimulationResult(
        plan=plan,
        success=True,
        measurements=[
            SimulationMeasurement(name="frequency_khz", value=12.5, unit="kHz", passed=True),
        ],
    )
    refinement = build_refinement_from_simulation(
        {"stage_id": 1, "stage_key": "basic_oscillation", "determinations": {}},
        result,
        approved=True,
    )
    assert refinement.approved is True
    assert "frequency_khz" in refinement.validated_determinations


def test_merge_refinement_into_stage_requires_approval() -> None:
    payload = {"stage_id": 1, "stage_key": "basic_oscillation", "determinations": {}}
    refinement = build_refinement_from_simulation(
        payload,
        SimulationResult(
            plan=SimulationPlan(stage_id=1, stage_key="basic_oscillation"),
            success=True,
        ),
        approved=False,
    )
    try:
        merge_refinement_into_stage(payload, refinement)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    refinement.approved = True
    merged = merge_refinement_into_stage(payload, refinement)
    assert "simulation_validation" in merged["determinations"]
