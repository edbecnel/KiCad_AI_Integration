"""Persist simulation run artifacts and EKM-ready measurement references (ADP-006)."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from context.collector import _resolve_project_file
from inference.simulation_types import SimulationResult
from utils.hashing import sha256_file


@dataclass
class SimulationArtifactRef:
    """Project-local artifact reference for closed-loop EKM write-back."""

    id: str
    kind: str
    path: str
    sha256: str
    label: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "kind": self.kind,
            "path": self.path,
            "sha256": self.sha256,
            "label": self.label or self.kind,
        }


def _utc_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def simulation_runs_index_path(project_path: Path | str) -> Path:
    pro = _resolve_project_file(Path(project_path))
    return pro.parent / "kicad_ai" / "simulation_runs.json"


def persist_simulation_run(
    project_path: Path | str,
    result: SimulationResult,
    *,
    netlist_path: Path | None = None,
    log_path: Path | None = None,
) -> list[SimulationArtifactRef]:
    """Write run artifacts under kicad_ai/exports/simulation/ and update index."""
    pro = _resolve_project_file(Path(project_path))
    run_id = _utc_run_id()
    run_dir = pro.parent / "kicad_ai" / "exports" / "simulation" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    refs: list[SimulationArtifactRef] = []

    result_path = run_dir / "result.json"
    result_path.write_text(
        json.dumps(result.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )
    refs.append(
        SimulationArtifactRef(
            id=f"sim-{run_id}-result",
            kind="simulation_result",
            path=str(result_path.relative_to(pro.parent)),
            sha256=sha256_file(result_path),
            label="Simulation result JSON",
        )
    )

    if netlist_path is not None and netlist_path.is_file():
        dest = run_dir / "netlist.cir"
        if netlist_path.resolve() != dest.resolve():
            shutil.copy2(netlist_path, dest)
        refs.append(
            SimulationArtifactRef(
                id=f"sim-{run_id}-netlist",
                kind="spice_netlist",
                path=str(dest.relative_to(pro.parent)),
                sha256=sha256_file(dest),
                label="SPICE netlist",
            )
        )

    if log_path is not None and log_path.is_file():
        dest = run_dir / "solver.log"
        if log_path.resolve() != dest.resolve():
            shutil.copy2(log_path, dest)
        refs.append(
            SimulationArtifactRef(
                id=f"sim-{run_id}-log",
                kind="solver_log",
                path=str(dest.relative_to(pro.parent)),
                sha256=sha256_file(dest),
                label="Solver log",
            )
        )

    for index, waveform in enumerate(result.waveform_paths):
        wave = Path(waveform)
        if not wave.is_file():
            continue
        dest = run_dir / f"waveform_{index}{wave.suffix or '.dat'}"
        shutil.copy2(wave, dest)
        refs.append(
            SimulationArtifactRef(
                id=f"sim-{run_id}-wave-{index}",
                kind="waveform",
                path=str(dest.relative_to(pro.parent)),
                sha256=sha256_file(dest),
                label=f"Waveform {index + 1}",
            )
        )

    _append_run_index(pro, run_id, result, refs)
    result.artifact_references = [r.to_dict() for r in refs]
    return refs


def _append_run_index(
    pro_path: Path,
    run_id: str,
    result: SimulationResult,
    refs: list[SimulationArtifactRef],
) -> None:
    index_path = simulation_runs_index_path(pro_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {"runs": []}
    if index_path.is_file():
        try:
            loaded = json.loads(index_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and isinstance(loaded.get("runs"), list):
                payload = loaded
        except (OSError, json.JSONDecodeError):
            pass
    payload["runs"].append(
        {
            "run_id": run_id,
            "success": result.success,
            "stage_id": result.plan.stage_id,
            "stage_key": result.plan.stage_key,
            "artifact_refs": [r.to_dict() for r in refs],
            "measurement_count": len(result.measurements),
            "created_at": run_id,
        }
    )
    payload["runs"] = payload["runs"][-20:]
    index_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
