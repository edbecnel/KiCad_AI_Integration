"""Tests for schematic connectivity parsing."""

from pathlib import Path

from context.schematic_connectivity import parse_schematic_labels

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
