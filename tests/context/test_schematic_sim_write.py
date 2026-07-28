"""Tests for KiCad 9 simulation field helpers."""

from __future__ import annotations

from pathlib import Path

from context.schematic_sim_write import (
    build_sim_pins_mapping,
    kicad9_sim_hookup_incomplete,
    parse_subckt_name_and_pins,
    parse_lib_symbol_pin_names,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
BABCOCK = Path("/Users/edbecnel/Development/Local/kicad_test_projects/Babcock-Patent-Driver-PCB-4p/Babcock-Patent-Driver-PCB-4p.kicad_sch")


def test_parse_subckt_name_and_pins() -> None:
    lib = """
.SUBCKT AC3M0160120D drain gate source
R1 drain gate 1
.ENDS
"""
    name, pins = parse_subckt_name_and_pins(lib, "AC3M0160120D")
    assert name == "AC3M0160120D"
    assert pins == ["drain", "gate", "source"]


def test_build_sim_pins_mapping_mosfet_gds() -> None:
    mapping = build_sim_pins_mapping(
        {"1": "G", "2": "D", "3": "S"},
        ["drain", "gate", "source"],
    )
    assert mapping == "1=gate 2=drain 3=source"


def test_kicad9_sim_hookup_incomplete_detects_empty_lib_in_params() -> None:
    assert kicad9_sim_hookup_incomplete(
        spice_lib="/tmp/AC3M0160120D.lib",
        sim_device="SPICE",
        sim_params='type="X" model="AC3M0160120D" lib=""',
    )


def test_kicad9_sim_hookup_complete_when_subckt_fields_set() -> None:
    assert not kicad9_sim_hookup_incomplete(
        spice_lib="/tmp/AC3M0160120D.lib",
        sim_device="SUBCKT",
        sim_library="/tmp/AC3M0160120D.lib",
        sim_name="AC3M0160120D",
        sim_pins="1=gate 2=drain 3=source",
    )


def test_kicad9_sim_hookup_incomplete_when_subckt_missing_pins() -> None:
    assert kicad9_sim_hookup_incomplete(
        spice_lib="/tmp/AC3M0160120D.lib",
        sim_device="SUBCKT",
        sim_library="/tmp/AC3M0160120D.lib",
        sim_name="AC3M0160120D",
    )


def test_kicad9_sim_hookup_incomplete_when_spice_device() -> None:
    assert kicad9_sim_hookup_incomplete(
        spice_lib="/tmp/AC3M0160120D.lib",
        sim_device="SPICE",
        sim_params='type="X" model="AC3M0160120D" lib=""',
    )


def test_parse_lib_symbol_pin_names_from_babcock_fixture() -> None:
    if not BABCOCK.is_file():
        return
    content = BABCOCK.read_text(encoding="utf-8")
    pins = parse_lib_symbol_pin_names(content, "Transistor_FET:C2M0025120D")
    assert pins == {"1": "G", "2": "D", "3": "S"}
