"""Tests for context.live.enrich."""

from __future__ import annotations

from pathlib import Path

from context.live.enrich import enrich_live_context
from context.model import ProjectContext


def test_enrich_live_context_firmware(blocking_oscillator_pro: Path, tmp_path: Path) -> None:
    fw = tmp_path / "main.py"
    fw.write_text("print('hello')\n", encoding="utf-8")
    ctx = ProjectContext(
        project_path=str(blocking_oscillator_pro),
        project_name="demo",
    )
    enriched = enrich_live_context(
        ctx,
        blocking_oscillator_pro,
        firmware_path=fw,
    )
    assert enriched.firmware_summary is not None
    assert enriched.firmware_summary["available"] is True
    assert "hello" in enriched.firmware_summary["text"]


def test_enrich_live_context_no_live_data(blocking_oscillator_pro: Path) -> None:
    ctx = ProjectContext(
        project_path=str(blocking_oscillator_pro),
        project_name="demo",
    )
    enriched = enrich_live_context(ctx, blocking_oscillator_pro)
    assert enriched.live_context is None or enriched.live_source is None
