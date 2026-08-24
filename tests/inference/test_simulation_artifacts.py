"""Tests for simulation artifact persistence (ADP-006 EKM refs)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from inference.simulation_artifacts import persist_simulation_run, simulation_runs_index_path
from inference.simulation_types import SimulationMeasurement, SimulationPlan, SimulationPlanStep, SimulationHook, SimulationResult


def test_persist_simulation_run_writes_index(blocking_oscillator_pro: Path, tmp_path: Path) -> None:
    hook = SimulationHook(description="Transient test", validates="startup")
    plan = SimulationPlan(stage_id=2, stage_key="energy_flow", steps=[SimulationPlanStep(hook=hook)])
    result = SimulationResult(
        plan=plan,
        success=True,
        measurements=[SimulationMeasurement(name="v_out", value=3.3, unit="V", passed=True)],
    )
    netlist = tmp_path / "test.cir"
    netlist.write_text(".title t\n.end\n", encoding="utf-8")
    refs = persist_simulation_run(blocking_oscillator_pro, result, netlist_path=netlist)
    assert refs
    assert result.artifact_references
    index_path = simulation_runs_index_path(blocking_oscillator_pro)
    assert index_path.is_file()
    assert "runs" in index_path.read_text(encoding="utf-8")
