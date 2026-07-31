"""Tests for simulation supply UI helpers."""

from __future__ import annotations

from pathlib import Path

from context.schematic_write import format_builtin_sim_write_message
from ui.simulation_supply import (
    GAP_LABELS,
    apply_builtin_simulation_models_panel,
    get_simulation_panel_context,
)
from utils.config import AppConfig

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


def test_apply_builtin_simulation_models_panel_writes_diode(tmp_path: Path) -> None:
    sch = tmp_path / "testproj.kicad_sch"
    sch.write_text((FIXTURES / "testproj.kicad_sch").read_text(encoding="utf-8"), encoding="utf-8")
    pro = tmp_path / "testproj.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    sch.write_text(
        sch.read_text(encoding="utf-8")
        + """
\t(symbol
\t\t(lib_id "Diode:1N4007")
\t\t(at 10 10 0)
\t\t(property "Reference" "D9"
\t\t\t(at 10 10 0)
\t\t)
\t\t(property "Value" "1N4007"
\t\t\t(at 10 10 0)
\t\t)
\t\t(property "Sim.Device" "D"
\t\t\t(at 10 10 0)
\t\t)
\t\t(property "Sim.Pins" "1=K 2=A"
\t\t\t(at 10 10 0)
\t\t)
\t\t(pin "1" (uuid "a"))
\t\t(pin "2" (uuid "b"))
\t)
""",
        encoding="utf-8",
    )
    cfg = AppConfig(
        artifact_library_path=tmp_path / "library",
        spice_write_symbol_fields=False,
    )
    panel, result = apply_builtin_simulation_models_panel(pro, config=cfg, verbose=False)
    assert result.changed_count >= 1
    d9 = next(s for s in panel.ctx.symbols if s.reference == "D9")
    assert d9.spice_model == "1N4007"
    message = format_builtin_sim_write_message(result)
    assert "D9" in message
    assert "symbol(s) updated" in message
