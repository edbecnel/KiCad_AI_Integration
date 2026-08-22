"""Tests for project metadata reader."""

from pathlib import Path

from context.project_metadata import read_project_metadata

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_read_project_metadata_testproj() -> None:
    meta = read_project_metadata(FIXTURES / "testproj.kicad_pro")
    assert meta["project_name"] == "testproj"
    assert "testproj.kicad_sch" in meta["schematic_files"]
    assert meta["root_schematic"] == "testproj.kicad_sch"
