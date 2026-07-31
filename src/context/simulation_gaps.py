"""Detect missing SPICE / SUBCKT simulation models for schematic symbols."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from context.artifacts.store import ArtifactStore
from context.builtin_sim_models import (
    kicad_simulation_model_incomplete,
    participates_in_simulation,
    resolve_builtin_simulation_hookup,
)
from context.datasheet_requirements import classify_datasheet_requirement
from context.datasheet_resolver import DatasheetResolution
from context.schematic_parse import SymbolInstance
from context.schematic_sim_write import kicad9_sim_hookup_incomplete

SimulationGapKind = Literal[
    "ok",
    "missing_spice_model",
    "unresolved_spice_lib",
    "has_lib_no_hookup",
    "kicad9_sim_incomplete",
    "netlist_missing_include",
]

_GAP_RANK: dict[SimulationGapKind, int] = {
    "ok": 0,
    "has_lib_no_hookup": 1,
    "kicad9_sim_incomplete": 2,
    "unresolved_spice_lib": 3,
    "netlist_missing_include": 4,
    "missing_spice_model": 5,
}


@dataclass
class SimulationGapRow:
    """One part Value grouped across schematic references."""

    part: str
    references: list[str]
    reference_count: int
    gap_kind: SimulationGapKind
    gap_detail: str
    spice_model: str = ""
    spice_lib: str = ""
    sim_device: str = ""
    tier_hint: str = "C"
    datasheet_resolved: bool = False
    catalog_lib_path: str | None = None
    catalog_lib_id: str | None = None
    netlist_includes: list[str] = field(default_factory=list)
    unresolved_includes: list[str] = field(default_factory=list)


def needs_subckt_model(symbol: SymbolInstance) -> bool:
    """True when the symbol typically needs a custom SUBCKT rather than a built-in."""
    return classify_datasheet_requirement(symbol) == "required"


def _classify_builtin_gap(sym: SymbolInstance) -> tuple[SimulationGapKind, str] | None:
    if not kicad_simulation_model_incomplete(sym):
        return ("ok", "")
    if resolve_builtin_simulation_hookup(sym, "") is not None:
        return (
            "missing_spice_model",
            "Built-in KiCad simulation model not configured (auto-apply on refresh)",
        )
    return (
        "missing_spice_model",
        "Simulation model not configured",
    )


def parse_spice_netlist_includes(netlist_text: str) -> list[str]:
    """Return paths from ``.include`` / ``.lib`` lines in a SPICE netlist."""
    includes: list[str] = []
    for line in netlist_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("."):
            continue
        lower = stripped.lower()
        if lower.startswith(".include"):
            match = re.search(r'["\']?([^"\']+)["\']?\s*$', stripped, re.I)
            if match:
                includes.append(match.group(1).strip())
        elif lower.startswith(".lib"):
            parts = stripped.split(maxsplit=1)
            if len(parts) == 2:
                includes.append(parts[1].strip().strip("'\""))
    return includes


def _resolve_spice_lib_path(spice_lib: str, project_root: Path) -> Path | None:
    raw = spice_lib.strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (project_root / path).resolve()
    return path if path.is_file() else None


def _classify_symbol_gap(
    sym: SymbolInstance,
    *,
    project_root: Path,
    store: ArtifactStore | None,
    unresolved_includes: set[str],
) -> tuple[SimulationGapKind, str]:
    part = (sym.value or sym.reference).strip()
    spice_model = sym.spice_model.strip()
    spice_lib = sym.spice_lib.strip()

    catalog_lib: Path | None = None
    if store is not None:
        entries = store.get_by_part(part, "lib")
        if entries:
            catalog_lib = store.resolve_local_path(entries[0].id)

    if spice_lib:
        resolved = _resolve_spice_lib_path(spice_lib, project_root)
        if resolved is None:
            return "unresolved_spice_lib", f"Spice_Lib not found on disk: {spice_lib}"
        if not spice_model:
            return "has_lib_no_hookup", "Spice_Lib set but Spice_Model is empty"

    if catalog_lib and not spice_model:
        if kicad9_sim_hookup_incomplete(
            spice_lib=str(catalog_lib),
            sim_library=sym.sim_library,
            sim_device=sym.sim_device,
            sim_name=sym.sim_name,
            sim_params=sym.sim_params,
            sim_pins=sym.sim_pins,
        ):
            return "kicad9_sim_incomplete", "Shared .lib exists; KiCad 9 Sim.* hookup needed"
        return "has_lib_no_hookup", f"Shared library has {catalog_lib.name} but Spice_Model is empty"

    if spice_model and kicad9_sim_hookup_incomplete(
        spice_lib=spice_lib or (str(catalog_lib) if catalog_lib else ""),
        sim_library=sym.sim_library,
        sim_device=sym.sim_device,
        sim_name=sym.sim_name,
        sim_params=sym.sim_params,
        sim_pins=sym.sim_pins,
    ):
        return (
            "kicad9_sim_incomplete",
            "Spice_Lib set but Simulation Model Editor is not linked (Sim.Library/Sim.Device)",
        )

    if spice_model:
        for inc in unresolved_includes:
            if part.lower() in inc.lower() or spice_model.lower() in inc.lower():
                return "netlist_missing_include", f"Netlist references missing file: {inc}"
        return "ok", ""

    builtin_gap = _classify_builtin_gap(sym)
    if builtin_gap is not None:
        return builtin_gap

    if unresolved_includes:
        for inc in unresolved_includes:
            if part.lower() in inc.lower():
                return "netlist_missing_include", f"Netlist references missing file: {inc}"

    return "missing_spice_model", "Spice_Model is empty and no shared .lib registered"


def summarize_simulation_gaps(
    symbols: list[SymbolInstance],
    *,
    project_root: Path,
    resolutions: dict[str, DatasheetResolution] | None = None,
    store: ArtifactStore | None = None,
    netlist_text: str | None = None,
    missing_only: bool = False,
) -> list[SimulationGapRow]:
    """Group symbols by Value and flag SPICE simulation model gaps."""
    includes = parse_spice_netlist_includes(netlist_text or "")
    unresolved: set[str] = set()
    for inc in includes:
        path = Path(inc).expanduser()
        if not path.is_absolute():
            path = (project_root / path).resolve()
        if not path.is_file():
            unresolved.add(inc)

    grouped: dict[str, dict[str, object]] = {}
    for sym in symbols:
        if not participates_in_simulation(sym):
            continue
        part = (sym.value or sym.reference).strip()
        res = (resolutions or {}).get(sym.reference)
        tier_hint = res.tier_hint if res else "C"
        datasheet_resolved = bool(res and res.status == "resolved")
        gap_kind, gap_detail = _classify_symbol_gap(
            sym,
            project_root=project_root,
            store=store,
            unresolved_includes=unresolved,
        )
        bucket = grouped.setdefault(
            part,
            {
                "part": part,
                "references": [],
                "gap_kind": "ok",
                "gap_detail": "",
                "spice_model": sym.spice_model.strip(),
                "spice_lib": sym.spice_lib.strip(),
                "sim_device": sym.sim_device.strip(),
                "tier_hint": tier_hint,
                "datasheet_resolved": datasheet_resolved,
                "catalog_lib_path": None,
                "catalog_lib_id": None,
                "netlist_includes": includes,
                "unresolved_includes": sorted(unresolved),
            },
        )
        refs = bucket["references"]
        assert isinstance(refs, list)
        refs.append(sym.reference)
        current = str(bucket["gap_kind"])
        if _GAP_RANK[gap_kind] > _GAP_RANK[current]:  # type: ignore[index]
            bucket["gap_kind"] = gap_kind
            bucket["gap_detail"] = gap_detail
        if sym.spice_model.strip() and not bucket["spice_model"]:
            bucket["spice_model"] = sym.spice_model.strip()
        if sym.spice_lib.strip() and not bucket["spice_lib"]:
            bucket["spice_lib"] = sym.spice_lib.strip()
        if sym.sim_device.strip() and not bucket["sim_device"]:
            bucket["sim_device"] = sym.sim_device.strip()
        if store is not None:
            entries = store.get_by_part(part, "lib")
            if entries and bucket["catalog_lib_path"] is None:
                local = store.resolve_local_path(entries[0].id)
                bucket["catalog_lib_path"] = str(local) if local else None
                bucket["catalog_lib_id"] = entries[0].id

    rows: list[SimulationGapRow] = []
    for part in sorted(grouped):
        entry = grouped[part]
        gap_kind = entry["gap_kind"]
        assert isinstance(gap_kind, str)
        if missing_only and gap_kind == "ok":
            continue
        refs = entry["references"]
        assert isinstance(refs, list)
        rows.append(
            SimulationGapRow(
                part=part,
                references=refs,
                reference_count=len(refs),
                gap_kind=gap_kind,  # type: ignore[arg-type]
                gap_detail=str(entry["gap_detail"]),
                spice_model=str(entry["spice_model"]),
                spice_lib=str(entry["spice_lib"]),
                sim_device=str(entry.get("sim_device", "")),
                tier_hint=str(entry["tier_hint"]),
                datasheet_resolved=bool(entry["datasheet_resolved"]),
                catalog_lib_path=(
                    str(entry["catalog_lib_path"]) if entry["catalog_lib_path"] else None
                ),
                catalog_lib_id=(
                    str(entry["catalog_lib_id"]) if entry["catalog_lib_id"] else None
                ),
                netlist_includes=list(entry["netlist_includes"]),  # type: ignore[arg-type]
                unresolved_includes=list(entry["unresolved_includes"]),  # type: ignore[arg-type]
            )
        )
    return rows
