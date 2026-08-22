"""Tests for netlist gap-fill prompt template."""

from pathlib import Path

from context.collector import collect_stretch_context
from prompts.builder import build_netlist_gap_fill_prompt
from utils.config import AppConfig

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_build_netlist_gap_fill_prompt(tmp_path: Path) -> None:
    cfg = AppConfig(artifact_library_path=tmp_path / "library")
    ctx = collect_stretch_context(
        FIXTURES / "blocking_oscillator.kicad_pro",
        config=cfg,
        verbose=False,
    )
    built = build_netlist_gap_fill_prompt(
        ctx,
        "Infer missing pin connections for the blocking oscillator.",
    )
    assert built.template == "netlist_gap_fill"
    assert "gap_fill_task" in built.text
    assert "connectivity_gaps" in built.text or "unconnected" in built.text.lower()
