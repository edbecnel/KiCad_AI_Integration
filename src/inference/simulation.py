"""Simulation / SUBCKT gap-fill inference workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from context.artifacts.store import ArtifactStore
from context.collector import _resolve_project_file, collect_stretch_context
from context.model import ProjectContext
from context.schematic_write import (
    SpiceFieldWriteResult,
    write_spice_fields_for_part,
)
from context.schematic_sim_write import load_subckt_metadata
from context.simulation_gaps import SimulationGapRow, summarize_simulation_gaps
from context.subckt_generation import SubcktGenerationResult, generate_subckt_for_part
from utils.config import AppConfig, load_config

GAP_LABELS = {
    "ok": "OK",
    "missing_spice_model": "Missing Spice_Model",
    "unresolved_spice_lib": "Unresolved Spice_Lib",
    "has_lib_no_hookup": "Lib available — hookup needed",
    "kicad9_sim_incomplete": "KiCad 9 sim hookup needed",
    "netlist_missing_include": "Netlist missing .include",
}


@dataclass
class SimulationPanelContext:
    project_path: Path
    ctx: ProjectContext
    rows_missing: list[SimulationGapRow]
    rows_all: list[SimulationGapRow]


def get_simulation_panel_context(
    project_path: Path,
    *,
    config: AppConfig | None = None,
    verbose: bool = False,
) -> SimulationPanelContext:
    """Collect project context and simulation gap rows."""
    cfg = config or load_config()
    pro_path = _resolve_project_file(project_path)
    ctx = collect_stretch_context(pro_path, config=cfg, verbose=verbose)
    store = ArtifactStore(cfg.artifact_library_path)
    project_root = pro_path.parent
    netlist_text = None
    if ctx.netlist_summary and isinstance(ctx.netlist_summary, dict):
        netlist_text = ctx.netlist_summary.get("text")
    rows_all = summarize_simulation_gaps(
        ctx.symbols,
        project_root=project_root,
        resolutions=ctx.datasheet_resolutions,
        store=store,
        netlist_text=str(netlist_text) if netlist_text else None,
        missing_only=False,
    )
    rows_missing = [r for r in rows_all if r.gap_kind != "ok"]
    return SimulationPanelContext(
        project_path=pro_path,
        ctx=ctx,
        rows_missing=rows_missing,
        rows_all=rows_all,
    )


def run_subckt_generation(
    project_path: Path,
    part: str,
    *,
    config: AppConfig | None = None,
    tier: str | None = None,
    verbose: bool = False,
) -> tuple[SimulationPanelContext, SubcktGenerationResult]:
    """Generate SUBCKT .lib for one part and refresh gap rows."""
    panel = get_simulation_panel_context(project_path, config=config, verbose=verbose)
    cfg = config or load_config()
    store = ArtifactStore(cfg.artifact_library_path)
    result = generate_subckt_for_part(
        panel.project_path,
        panel.ctx,
        part,
        config=cfg,
        store=store,
        tier=tier,  # type: ignore[arg-type]
    )
    refreshed = get_simulation_panel_context(project_path, config=cfg, verbose=False)
    return refreshed, result


def apply_spice_fields_for_part(
    project_path: Path,
    part: str,
    *,
    spice_model: str,
    spice_lib: str,
    spice_primitive: str = "X",
    config: AppConfig | None = None,
    verbose: bool = False,
) -> tuple[SimulationPanelContext, SpiceFieldWriteResult]:
    """Write Spice fields to schematic for one part Value."""
    panel = get_simulation_panel_context(project_path, config=config, verbose=verbose)
    result = write_spice_fields_for_part(
        panel.project_path,
        panel.ctx,
        part=part,
        spice_model=spice_model,
        spice_lib=spice_lib,
        spice_primitive=spice_primitive,
    )
    return panel, result


def apply_simulation_model_for_part(
    project_path: Path,
    part: str,
    *,
    config: AppConfig | None = None,
    verbose: bool = False,
) -> tuple[SimulationPanelContext, SpiceFieldWriteResult | None]:
    """Write KiCad 9 Sim.* + legacy Spice_* for one part."""
    cfg = config or load_config()
    panel = get_simulation_panel_context(project_path, config=cfg, verbose=verbose)
    part_norm = part.strip()
    store = ArtifactStore(cfg.artifact_library_path)

    lib_path: Path | None = None
    entries = store.get_by_part(part_norm, "lib")
    if entries:
        lib_path = store.resolve_local_path(entries[0].id)

    if lib_path is None:
        for sym in panel.ctx.symbols:
            if (sym.value or sym.reference).strip() != part_norm:
                continue
            candidate = sym.spice_lib.strip()
            if candidate:
                lib_path = Path(candidate).expanduser()
                if lib_path.is_file():
                    break
                lib_path = None

    if lib_path is None or not lib_path.is_file():
        return panel, None

    subckt_name, _pins = load_subckt_metadata(lib_path, part_norm)
    result = write_spice_fields_for_part(
        panel.project_path,
        panel.ctx,
        part=part_norm,
        spice_model=subckt_name,
        spice_lib=str(lib_path),
    )
    refreshed = get_simulation_panel_context(project_path, config=cfg, verbose=False)
    return refreshed, result


def apply_spice_fields_from_catalog(
    project_path: Path,
    part: str,
    *,
    config: AppConfig | None = None,
    verbose: bool = False,
) -> tuple[SimulationPanelContext, SpiceFieldWriteResult | None]:
    """Write simulation model fields using catalog or schematic Spice_Lib."""
    return apply_simulation_model_for_part(
        project_path,
        part,
        config=config,
        verbose=verbose,
    )
