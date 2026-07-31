"""Tests for simulation gap detection."""

from __future__ import annotations

from pathlib import Path

from context.artifacts.catalog import ComponentRef
from context.artifacts.store import ArtifactStore, ProjectContextInfo
from context.datasheet_resolver import DatasheetResolution
from context.schematic_parse import SymbolInstance, parse_project_schematics
from context.simulation_gaps import (
    parse_spice_netlist_includes,
    summarize_simulation_gaps,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_parse_spice_netlist_includes() -> None:
    text = '.include "models/FOD3180.lib"\n.lib vendor.lib\n'
    assert parse_spice_netlist_includes(text) == ["models/FOD3180.lib", "vendor.lib"]


def test_summarize_simulation_gaps_flags_missing_spice_model(tmp_path: Path) -> None:
    pro = tmp_path / "testproj.kicad_pro"
    pro.touch()
    sch = tmp_path / "testproj.kicad_sch"
    sch.write_text((FIXTURES / "testproj.kicad_sch").read_text(encoding="utf-8"), encoding="utf-8")
    symbols = parse_project_schematics(tmp_path, [sch])
    resolutions = {
        "U3": DatasheetResolution(
            status="resolved",
            reference="U3",
            part="F0D3180",
            tier_hint="A",
        )
    }
    rows = summarize_simulation_gaps(
        symbols,
        project_root=tmp_path,
        resolutions=resolutions,
        missing_only=True,
    )
    fod = next(r for r in rows if r.part == "F0D3180")
    assert fod.gap_kind == "missing_spice_model"
    assert fod.tier_hint == "A"


def test_summarize_simulation_gaps_has_lib_no_hookup(tmp_path: Path) -> None:
    pro = tmp_path / "testproj.kicad_pro"
    pro.touch()
    sch = tmp_path / "testproj.kicad_sch"
    sch.write_text((FIXTURES / "testproj.kicad_sch").read_text(encoding="utf-8"), encoding="utf-8")
    symbols = parse_project_schematics(tmp_path, [sch])
    lib = tmp_path / "lib"
    store = ArtifactStore(lib)
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[sch])
    lib_file = tmp_path / "F0D3180.lib"
    lib_file.write_text(".SUBCKT F0D3180 1 2\n.ENDS\n", encoding="utf-8")
    store.register_lib(
        lib_file,
        "F0D3180",
        "ai_subckt",
        project,
        ComponentRef(reference="U3", sheet_path="testproj.kicad_sch"),
        tier="datasheet_backed",
    )
    rows = summarize_simulation_gaps(
        symbols,
        project_root=tmp_path,
        store=store,
        missing_only=True,
    )
    fod = next(r for r in rows if r.part == "F0D3180")
    assert fod.gap_kind == "kicad9_sim_incomplete"
    assert "KiCad 9" in fod.gap_detail
    assert fod.catalog_lib_path is not None
