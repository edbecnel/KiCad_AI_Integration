"""Tests for minimal PCB summary."""

from pathlib import Path

from context.pcb_summary import collect_pcb_summary


def test_collect_pcb_summary_none_without_pcb(tmp_path: Path) -> None:
    pro = tmp_path / "board.kicad_pro"
    pro.touch()
    assert collect_pcb_summary(pro) is None


def test_collect_pcb_summary_counts(tmp_path: Path) -> None:
    pro = tmp_path / "board.kicad_pro"
    pro.touch()
    pcb = tmp_path / "board.kicad_pcb"
    pcb.write_text(
        '(kicad_pcb (footprint "R1" (net 1)) (footprint "C1" (net 2)) (net 1 "+5V"))\n',
        encoding="utf-8",
    )
    summary = collect_pcb_summary(pro)
    assert summary is not None
    assert summary["footprint_count"] == 2
    assert summary["net_count"] == 1
