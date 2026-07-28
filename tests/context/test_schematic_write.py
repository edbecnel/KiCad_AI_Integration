"""Tests for writing Datasheet properties back to .kicad_sch files."""

from __future__ import annotations

from pathlib import Path

import pytest

from context.artifacts.catalog import ComponentRef
from context.artifacts.store import ArtifactStore, ProjectContextInfo
from context.datasheet_resolver import DatasheetResolution
from context.model import ProjectContext
from context.schematic_parse import parse_schematic_symbols
from context.schematic_write import (
    update_symbol_datasheet_property,
    write_resolved_datasheet_urls,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_update_symbol_datasheet_property_replaces_existing(tmp_path: Path) -> None:
    sch = tmp_path / "test.kicad_sch"
    sch.write_text((FIXTURES / "minimal.kicad_sch").read_text(encoding="utf-8"), encoding="utf-8")
    url = "https://example.com/f0d3180.pdf"
    assert update_symbol_datasheet_property(sch, "U3", url) is True
    symbols = parse_schematic_symbols(sch)
    u3 = next(s for s in symbols if s.reference == "U3")
    assert u3.datasheet == url


def test_write_spice_fields_for_part(tmp_path: Path) -> None:
    from context.schematic_write import write_spice_fields_for_part

    sch = tmp_path / "test.kicad_sch"
    sch.write_text((FIXTURES / "testproj.kicad_sch").read_text(encoding="utf-8"), encoding="utf-8")
    pro = tmp_path / "test.kicad_pro"
    pro.touch()
    lib_file = tmp_path / "F0D3180.lib"
    lib_file.write_text(
        ".SUBCKT F0D3180 A C E NC1 NC4 VEE OUT6 OUT7 VCC\n.ENDS\n",
        encoding="utf-8",
    )
    symbols = parse_schematic_symbols(sch)
    ctx = ProjectContext(
        project_path=str(pro),
        project_name="test",
        schematics=["test.kicad_sch"],
        symbols=symbols,
    )
    result = write_spice_fields_for_part(
        pro,
        ctx,
        part="F0D3180",
        spice_model="F0D3180",
        spice_lib=str(lib_file),
        spice_primitive="X",
    )
    assert result.changed_count == 1
    updated = parse_schematic_symbols(sch)
    u3 = next(s for s in updated if s.reference == "U3")
    assert u3.spice_model == "F0D3180"
    assert u3.spice_lib == str(lib_file)
    assert u3.sim_device == "SUBCKT"
    assert u3.sim_library == str(lib_file)
    assert u3.sim_name == "F0D3180"
    assert u3.sim_pins
    content = sch.read_text(encoding="utf-8")
    assert '(property "Sim.Device" "SUBCKT"' in content
    assert "Sim.Params" not in content.split("U3")[1].split("symbol")[0] if "U3" in content else True


def test_write_resolved_datasheet_urls_from_catalog_source(tmp_path: Path) -> None:
    sch = tmp_path / "test.kicad_sch"
    sch.write_text((FIXTURES / "minimal.kicad_sch").read_text(encoding="utf-8"), encoding="utf-8")
    pro = tmp_path / "test.kicad_pro"
    pro.touch()
    lib = tmp_path / "lib"
    store = ArtifactStore(lib)
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[sch])
    pdf = tmp_path / "fod.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    url = "https://onsemi.com/fod3180.pdf"
    entry = store.register_datasheet(
        pdf,
        "F0D3180",
        "https_fetch",
        project,
        ComponentRef(reference="U3", sheet_path="test.kicad_sch"),
        source_url=url,
    )
    ctx = ProjectContext(
        project_path=str(pro),
        project_name="test",
        schematics=["test.kicad_sch"],
        symbols=parse_schematic_symbols(sch),
        datasheet_resolutions={
            "U3": DatasheetResolution(
                status="resolved",
                artifact_id=entry.id,
                reference="U3",
                part="F0D3180",
            )
        },
    )
    result = write_resolved_datasheet_urls(pro, ctx, store, part="F0D3180")
    assert result.changed_count == 1
    u3 = next(s for s in parse_schematic_symbols(sch) if s.reference == "U3")
    assert u3.datasheet == url


def test_write_skips_when_only_if_empty_and_field_set(tmp_path: Path) -> None:
    sch = tmp_path / "test.kicad_sch"
    sch.write_text((FIXTURES / "minimal.kicad_sch").read_text(encoding="utf-8"), encoding="utf-8")
    pro = tmp_path / "test.kicad_pro"
    pro.touch()
    store = ArtifactStore(tmp_path / "lib")
    ctx = ProjectContext(
        project_path=str(pro),
        project_name="test",
        schematics=["test.kicad_sch"],
        symbols=parse_schematic_symbols(sch),
        datasheet_resolutions={
            "U3": DatasheetResolution(
                status="resolved",
                reference="U3",
                part="F0D3180",
            )
        },
    )
    result = write_resolved_datasheet_urls(pro, ctx, store, only_if_empty=True)
    assert result.changed_count == 0


def test_summarize_symbol_field_issues_detects_empty_and_mismatch(tmp_path: Path) -> None:
    from context.schematic_parse import SymbolInstance
    from context.schematic_write import summarize_symbol_field_issues

    store = ArtifactStore(tmp_path / "lib")
    symbols = [
        SymbolInstance(
            reference="U1",
            value="FOD3180",
            datasheet="",
            sheet_path="p.kicad_sch",
            lib_id="Opto:FOD3180",
        ),
        SymbolInstance(
            reference="U2",
            value="FOD3180",
            datasheet="https://old.example.com/fod.pdf",
            sheet_path="p.kicad_sch",
            lib_id="Opto:FOD3180",
        ),
    ]
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[tmp_path / "p.kicad_sch"])
    pdf = tmp_path / "f.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    url = "https://onsemi.com/fod3180.pdf"
    entry = store.register_datasheet(
        pdf,
        "FOD3180",
        "https_fetch",
        project,
        ComponentRef(reference="U2", sheet_path="p.kicad_sch"),
        source_url=url,
    )
    resolutions = {
        "U1": DatasheetResolution(status="missing", reference="U1", part="FOD3180"),
        "U2": DatasheetResolution(
            status="resolved",
            artifact_id=entry.id,
            reference="U2",
            part="FOD3180",
        ),
    }
    issues = summarize_symbol_field_issues(symbols, resolutions, store)
    assert len(issues) == 1
    assert issues[0]["part"] == "FOD3180"
    assert issues[0]["resolved_url"] == url
