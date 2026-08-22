"""Tests for DSN export adapter."""

from __future__ import annotations

from pathlib import Path

from context.dsn_export import export_specctra_dsn


def test_export_specctra_dsn_unavailable_without_pcbnew(tmp_path: Path) -> None:
    pcb = tmp_path / "board.kicad_pcb"
    pcb.write_text("(kicad_pcb)\n", encoding="utf-8")
    result = export_specctra_dsn(pcb, tmp_path / "board.dsn")
    assert result.status == "unavailable"
    assert "pcbnew" in result.message.lower()


def test_export_specctra_dsn_missing_pcb(tmp_path: Path) -> None:
    result = export_specctra_dsn(tmp_path / "missing.kicad_pcb", tmp_path / "board.dsn")
    assert result.status == "error"
