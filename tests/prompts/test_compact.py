"""Tests for prompt context compaction."""

from pathlib import Path

from context.collector import collect_stretch_context
from prompts.compact import compact_context_for_prompt
from utils.config import AppConfig

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_compact_unchanged_for_small_fixture(tmp_path: Path) -> None:
    ds_dir = FIXTURES / "datasheets"
    ds_dir.mkdir(exist_ok=True)
    (ds_dir / "F0D3180.pdf").write_bytes(b"%PDF-1.4 test")
    config = AppConfig(artifact_library_path=tmp_path / "library")
    ctx = collect_stretch_context(FIXTURES / "testproj.kicad_pro", config=config)
    data = compact_context_for_prompt(ctx)
    assert "symbols" in data
    assert "_note" not in data


def test_compact_large_symbol_list() -> None:
    from context.model import ProjectContext
    from context.schematic_parse import SymbolInstance

    symbols = [
        SymbolInstance(reference=f"R{i}", value=f"{i}k", sheet_path="x.kicad_sch")
        for i in range(60)
    ]
    ctx = ProjectContext(
        project_path="/p/p.kicad_pro",
        project_name="big",
        symbols=symbols,
    )
    data = compact_context_for_prompt(ctx)
    assert data["symbol_count"] == 60
    assert len(data["symbols"]) == 60
    assert "_note" in data
    assert "datasheet_summary" in data
