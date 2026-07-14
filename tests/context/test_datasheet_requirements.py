"""Tests for datasheet requirement classification."""

from context.datasheet_requirements import (
    classify_datasheet_requirement,
    needs_user_pdf,
)
from context.schematic_parse import SymbolInstance


def test_resistor_optional() -> None:
    sym = SymbolInstance(
        reference="R1",
        value="10k",
        lib_id="Device:R_Small_US",
        sheet_path="p.kicad_sch",
    )
    assert classify_datasheet_requirement(sym) == "optional"
    assert not needs_user_pdf("missing", "optional")


def test_power_not_applicable() -> None:
    sym = SymbolInstance(
        reference="#PWR01",
        value="+12",
        lib_id="power:+12VA",
        sheet_path="p.kicad_sch",
    )
    assert classify_datasheet_requirement(sym) == "not_applicable"


def test_fet_required() -> None:
    sym = SymbolInstance(
        reference="Q1",
        value="IRFP260MPBF",
        lib_id="Transistor_FET:C2M0025120D",
        footprint="TO-247",
        sheet_path="p.kicad_sch",
    )
    assert classify_datasheet_requirement(sym) == "required"
    assert needs_user_pdf("fetch_failed", "required")


def test_optocoupler_required() -> None:
    sym = SymbolInstance(
        reference="U2",
        value="FOD3180",
        lib_id="New_Library:FOD3180",
        sheet_path="p.kicad_sch",
    )
    assert classify_datasheet_requirement(sym) == "required"


def test_summarize_required_missing() -> None:
    from context.datasheet_resolver import DatasheetResolution

    sym = SymbolInstance(
        reference="U2",
        value="FOD3180",
        lib_id="New_Library:FOD3180",
        sheet_path="p.kicad_sch",
    )
    res = DatasheetResolution(
        reference="U2",
        part="FOD3180",
        status="fetch_failed",
        sources_tried=["fetch_error:HTTP 403 Forbidden"],
    )
    from context.datasheet_requirements import summarize_required_missing_datasheets

    rows = summarize_required_missing_datasheets([sym], {"U2": res})
    assert len(rows) == 1
    assert rows[0]["part"] == "FOD3180"
