"""Tests for PCB detail extraction."""

from __future__ import annotations

from pathlib import Path

from context.pcb_extract import collect_pcb_detail


def test_collect_pcb_detail_from_inline_fixture(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    pcb = tmp_path / "demo.kicad_pcb"
    pro.write_text("{}", encoding="utf-8")
    pcb.write_text(
        """
(kicad_pcb (version 20240108) (generator pcbnew)
  (net 1 "GND")
  (net 2 "VCC")
  (net_class "Default" (clearance 0.2) (track_width 0.25))
  (segment (start 0 0) (end 10 0) (width 0.25) (layer "F.Cu") (net 1))
  (segment (start 0 0) (end 0 10) (width 0.5) (layer "F.Cu") (net 2))
  (via (at 5 5) (size 0.8) (drill 0.4) (layers "F.Cu-B.Cu") (net 1))
  (zone (net 1) (layer "F.Cu"))
  (footprint "R1")
)
""",
        encoding="utf-8",
    )
    detail = collect_pcb_detail(pro)
    assert detail is not None
    assert detail["track_segment_count"] == 2
    assert detail["via_count"] == 1
    assert detail["zone_count"] == 1
    assert detail["footprint_count"] == 1
    assert detail["net_classes"][0]["name"] == "Default"
