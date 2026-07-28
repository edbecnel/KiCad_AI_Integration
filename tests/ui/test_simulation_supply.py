"""Tests for simulation supply UI helpers."""

from __future__ import annotations

from pathlib import Path

from ui.simulation_supply import GAP_LABELS, get_simulation_panel_context

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_gap_labels_cover_all_kinds() -> None:
    assert "missing_spice_model" in GAP_LABELS
    assert "has_lib_no_hookup" in GAP_LABELS
    assert "kicad9_sim_incomplete" in GAP_LABELS


def test_get_simulation_panel_context(tmp_path: Path) -> None:
    pro = tmp_path / "testproj.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    sch = tmp_path / "testproj.kicad_sch"
    sch.write_text((FIXTURES / "testproj.kicad_sch").read_text(encoding="utf-8"), encoding="utf-8")
    panel = get_simulation_panel_context(pro, verbose=False)
    assert panel.ctx.project_name == "testproj"
    assert any(r.part == "F0D3180" for r in panel.rows_all)
