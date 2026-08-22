"""Tests for static context cache."""

from __future__ import annotations

from pathlib import Path

from context.context_cache import (
    cache_matches_project,
    load_context_cache,
    save_context_cache,
    snapshot_from_context,
)
from context.model import ProjectContext


def test_snapshot_from_context_extracts_summary_fields() -> None:
    ctx = ProjectContext(
        project_path="/tmp/demo.kicad_pro",
        project_name="demo",
        symbols=[],
        netlist_summary={"status_line": "SPICE netlist: 5 lines"},
        bom_summary=[{"ref": "R1"}],
    )
    snap = snapshot_from_context(ctx)
    assert snap.symbol_count == 0
    assert snap.netlist_status_line == "SPICE netlist: 5 lines"
    assert snap.bom_line_count == 1


def test_save_and_load_context_cache(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    sch = tmp_path / "demo.kicad_sch"
    pro.write_text("{}", encoding="utf-8")
    sch.write_text("sch", encoding="utf-8")

    ctx = ProjectContext(
        project_path=str(pro),
        project_name="demo",
        symbols=[],
        netlist_summary={"status_line": "SPICE netlist: 2 lines"},
    )
    save_context_cache(pro, ctx, prompt_excerpt="hello")
    loaded = load_context_cache(pro)
    assert loaded is not None
    assert loaded.snapshot.project_name == "demo"
    assert cache_matches_project(pro)
