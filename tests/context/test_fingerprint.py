"""Tests for project file fingerprinting."""

from __future__ import annotations

import time
from pathlib import Path

from context.fingerprint import (
    compute_fingerprint,
    dirty_layers,
    load_fingerprint,
    project_changed_since,
    save_fingerprint,
)


def test_compute_fingerprint_includes_layers(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    sch = tmp_path / "demo.kicad_sch"
    pcb = tmp_path / "demo.kicad_pcb"
    pro.write_text("{}", encoding="utf-8")
    sch.write_text("(kicad_sch)", encoding="utf-8")
    pcb.write_text("(kicad_pcb)", encoding="utf-8")

    fp = compute_fingerprint(pro)
    assert fp.project_path == str(pro.resolve())
    assert fp.layers["schematic"]
    assert fp.layers["pcb"]
    assert fp.layers["netlist"]


def test_dirty_layers_detects_schematic_change(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    sch = tmp_path / "demo.kicad_sch"
    pro.write_text("{}", encoding="utf-8")
    sch.write_text("v1", encoding="utf-8")

    before = compute_fingerprint(pro)
    time.sleep(0.02)
    sch.write_text("v2", encoding="utf-8")
    after = compute_fingerprint(pro)

    dirty = dirty_layers(before, after)
    assert "schematic" in dirty
    assert project_changed_since(before, after)


def test_save_and_load_fingerprint(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    sch = tmp_path / "demo.kicad_sch"
    pro.write_text("{}", encoding="utf-8")
    sch.write_text("sch", encoding="utf-8")

    fp = compute_fingerprint(pro)
    save_fingerprint(fp)
    loaded = load_fingerprint(pro)
    assert loaded is not None
    assert loaded.layers == fp.layers
