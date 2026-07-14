"""Tests for schematic parsing."""

from pathlib import Path

from context.schematic_parse import (
    discover_schematic_paths,
    parse_project_schematics,
    parse_schematic_symbols,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_parse_minimal_symbols() -> None:
    sch = FIXTURES / "minimal.kicad_sch"
    symbols = parse_schematic_symbols(sch)
    refs = {s.reference for s in symbols}
    assert refs == {"R1", "U3"}
    u3 = next(s for s in symbols if s.reference == "U3")
    assert u3.value == "F0D3180"
    assert u3.datasheet == "datasheets/F0D3180.pdf"


def test_parse_hierarchical_project() -> None:
    root = FIXTURES
    sch_paths = discover_schematic_paths(root / "testproj.kicad_pro")
    assert sch_paths[0].name == "testproj.kicad_sch"
    symbols = parse_project_schematics(
        root,
        sch_paths,
        root_schematic=sch_paths[0],
    )
    refs = {s.reference for s in symbols}
    assert "U3" in refs
    assert "U1" in refs  # from power.kicad_sch subsheet
