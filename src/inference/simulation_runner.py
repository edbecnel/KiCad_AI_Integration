"""Host solver adapter for ADP-006 closed-loop simulation plans."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from context.collector import _resolve_project_file
from context.netlist_export import collect_netlist_summary
from inference.simulation_artifacts import persist_simulation_run
from inference.simulation_types import SimulationMeasurement, SimulationPlan, SimulationResult
from utils.config import AppConfig, load_config


def _ngspice_available() -> bool:
    return shutil.which("ngspice") is not None


def run_simulation_plan(
    project_path: Path | str,
    plan: SimulationPlan,
    *,
    config: AppConfig | None = None,
    timeout_sec: int = 120,
) -> SimulationResult:
    """
    Execute or stub-run a simulation plan.

    When ngspice is unavailable, returns a structured result with manual-run
    instructions rather than failing silently.
    """
    cfg = config or load_config()
    pro_path = _resolve_project_file(Path(project_path))
    netlist_path = pro_path.parent / "kicad_ai" / "exports" / "simulation" / "closed_loop.cir"
    netlist_path.parent.mkdir(parents=True, exist_ok=True)

    summary = collect_netlist_summary(pro_path, config=cfg)
    if summary and summary.get("text"):
        netlist_path.write_text(str(summary["text"]), encoding="utf-8")
    else:
        return SimulationResult(
            plan=plan,
            success=False,
            errors=["SPICE netlist export failed (kicad-cli unavailable or empty netlist)."],
        )

    if not _ngspice_available():
        result = SimulationResult(
            plan=plan,
            success=False,
            errors=[
                "ngspice not found on PATH — export netlist for manual KiCad Simulator run.",
            ],
            log_excerpt=f"Netlist written: {netlist_path}",
            measurements=[
                SimulationMeasurement(
                    name="manual_run_required",
                    value="true",
                    notes="Open netlist in KiCad Simulator or run: ngspice closed_loop.cir",
                )
            ],
        )
        persist_simulation_run(pro_path, result, netlist_path=netlist_path)
        return result

    log_path = netlist_path.with_suffix(".log")
    try:
        completed = subprocess.run(
            ["ngspice", "-b", str(netlist_path)],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return SimulationResult(
            plan=plan,
            success=False,
            errors=[f"ngspice execution failed: {exc}"],
            log_excerpt=str(netlist_path),
        )

    log_text = (completed.stdout or "") + "\n" + (completed.stderr or "")
    log_path.write_text(log_text, encoding="utf-8")
    success = completed.returncode == 0
    measurements = [
        SimulationMeasurement(
            name="ngspice_exit_code",
            value=completed.returncode,
            passed=success,
        )
    ]
    for step in plan.steps:
        measurements.append(
            SimulationMeasurement(
                name=f"hook_{step.hook.analysis_kind}",
                value="executed" if success else "failed",
                passed=success if step.hook.validates else None,
                notes=step.hook.description[:200],
            )
        )
    result = SimulationResult(
        plan=plan,
        success=success,
        measurements=measurements,
        log_excerpt=log_text[-2000:],
        errors=[] if success else [f"ngspice exited with code {completed.returncode}"],
    )
    persist_simulation_run(pro_path, result, netlist_path=netlist_path, log_path=log_path)
    return result


def run_closed_loop_for_stage(
    project_path: Path | str,
    stage_payload: dict[str, Any],
    *,
    config: AppConfig | None = None,
    approved_refinement: bool = False,
) -> tuple[SimulationResult | None, dict[str, Any] | None]:
    """Translate hooks, run solver, optionally merge approved refinement."""
    from inference.simulation_closed_loop import (
        build_refinement_from_simulation,
        merge_refinement_into_stage,
        translate_simulation_hooks,
    )

    plan = translate_simulation_hooks(stage_payload)
    if plan is None:
        return None, None
    result = run_simulation_plan(project_path, plan, config=config)
    refinement = build_refinement_from_simulation(
        stage_payload,
        result,
        approved=approved_refinement,
    )
    merged = None
    if approved_refinement:
        merged = merge_refinement_into_stage(stage_payload, refinement)
    return result, merged
