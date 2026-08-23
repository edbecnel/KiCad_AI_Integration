"""Tests for simulation runner (ADP-006 host wiring)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from inference.simulation_runner import run_simulation_plan
from inference.simulation_types import SimulationHook, SimulationPlan, SimulationPlanStep


def test_run_simulation_plan_without_ngspice(blocking_oscillator_pro: Path) -> None:
    hook = SimulationHook(description="Transient startup waveform", validates="Oscillation")
    plan = SimulationPlan(stage_id=2, stage_key="energy_flow", steps=[SimulationPlanStep(hook=hook)])
    with patch("inference.simulation_runner._ngspice_available", return_value=False):
        with patch(
            "inference.simulation_runner.collect_netlist_summary",
            return_value={"text": ".title test\nR1 1 2 1k\n.end", "line_count": 3, "export_status": "ok"},
        ):
            result = run_simulation_plan(blocking_oscillator_pro, plan)
    assert result.success is False
    assert any("ngspice" in err.lower() for err in result.errors)
