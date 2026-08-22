"""Tests for schematic connectivity parsing."""

from pathlib import Path

from context.schematic_connectivity import (
    build_pin_connectivity,
    connectivity_summary,
    parse_project_pins,
    parse_schematic_labels,
    parse_schematic_pins,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_parse_schematic_labels_empty_on_minimal_fixture() -> None:
    labels = parse_schematic_labels(FIXTURES / "minimal.kicad_sch")
    assert labels == []


def test_parse_schematic_labels_from_labeled_fixture(tmp_path: Path) -> None:
    sch = tmp_path / "labeled.kicad_sch"
    sch.write_text(
        '(kicad_sch (version 20250114)\n'
        '  (label "+12V" (at 10 10 0))\n'
        '  (global_label "GND" (at 20 20 0))\n'
        ")\n",
        encoding="utf-8",
    )
    labels = parse_schematic_labels(sch)
    assert len(labels) == 2
    names = {label.name for label in labels}
    assert "+12V" in names
    assert "GND" in names


def test_parse_schematic_pins_blocking_oscillator_fixture() -> None:
    pins = parse_schematic_pins(FIXTURES / "blocking_oscillator.kicad_sch")
    assert len(pins) >= 6
    q1_pins = [p for p in pins if p.reference == "Q1"]
    assert len(q1_pins) == 3


def test_build_pin_connectivity_lists_unconnected_without_netlist() -> None:
    from context.schematic_parse import parse_schematic_symbols

    symbols = parse_schematic_symbols(FIXTURES / "blocking_oscillator.kicad_sch")
    pins = parse_schematic_pins(FIXTURES / "blocking_oscillator.kicad_sch")
    pin_conn = build_pin_connectivity(symbols, pins, None)
    assert pin_conn["pin_count"] >= 6
    assert pin_conn["unconnected_count"] == pin_conn["pin_count"]
    summary = connectivity_summary([], pin_connectivity=pin_conn)
    assert summary["pin_connectivity"]["unconnected_count"] > 0
