"""Tests for incremental context refresh."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from context.context_flags import ContextIncludeFlags
from context.incremental import detect_dirty_layers, layers_for_flags, refresh_context_layers
from context.model import ProjectContext


def test_layers_for_flags_maps_ui_toggles() -> None:
    flags = ContextIncludeFlags(schematic=False, pcb=True, bom=False, erc_drc=False, netlist=True)
    layers = layers_for_flags(flags)
    assert "schematic" not in layers
    assert "pcb" in layers
    assert "netlist" in layers
    assert "bom" not in layers


def test_refresh_context_layers_calls_pcb_only(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    sch = tmp_path / "demo.kicad_sch"
    pro.write_text("{}", encoding="utf-8")
    sch.write_text("sch", encoding="utf-8")

    ctx = ProjectContext(project_path=str(pro), project_name="demo", symbols=[])
    with patch("context.pcb_summary.collect_pcb_summary", return_value={"status_line": "pcb ok"}) as pcb_mock:
        updated = refresh_context_layers(ctx, pro, {"pcb"})
    pcb_mock.assert_called_once()
    assert updated.pcb_summary == {"status_line": "pcb ok"}


def test_detect_dirty_layers_uses_stored_fingerprint(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    sch = tmp_path / "demo.kicad_sch"
    pro.write_text("{}", encoding="utf-8")
    sch.write_text("v1", encoding="utf-8")

    from context.fingerprint import compute_fingerprint, save_fingerprint

    save_fingerprint(compute_fingerprint(pro))
    sch.write_text("v2", encoding="utf-8")
    dirty = detect_dirty_layers(pro)
    assert "schematic" in dirty
