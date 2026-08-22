"""Tests for netlist gap-fill detection."""

from pathlib import Path

from context.collector import collect_stretch_context
from context.netlist_gap_fill import detect_connectivity_gaps, is_auto_generated_net
from context.schematic_connectivity import parse_project_pins
from context.schematic_parse import parse_project_schematics, discover_schematic_paths
from utils.config import AppConfig

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_is_auto_generated_net() -> None:
    assert is_auto_generated_net("Net-(D1-Pad2)")
    assert not is_auto_generated_net("+12V")


def test_detect_connectivity_gaps_blocking_oscillator(tmp_path: Path) -> None:
    cfg = AppConfig(artifact_library_path=tmp_path / "library")
    ctx = collect_stretch_context(
        FIXTURES / "blocking_oscillator.kicad_pro",
        config=cfg,
        verbose=False,
    )
    assert ctx.connectivity_gaps is not None
    assert "unconnected_pins" in ctx.connectivity_gaps
    assert ctx.connectivity_gaps.get("needs_connectivity_inference") is True


def test_detect_connectivity_gaps_with_auto_net() -> None:
    from context.schematic_parse import SymbolInstance

    sym = SymbolInstance(reference="R1", value="10k")
    graph = {
        "nets": ["Net-(R1-Pad1)", "GND"],
        "connections": [{"reference": "R1", "pin": "1", "net": "Net-(R1-Pad1)"}],
    }
    pro = FIXTURES / "blocking_oscillator.kicad_pro"
    paths = discover_schematic_paths(pro)
    pins = parse_project_pins(pro.parent, paths)
    symbols = parse_project_schematics(pro.parent, paths, root_schematic=paths[0])
    from context.schematic_connectivity import build_pin_connectivity

    pin_conn = build_pin_connectivity(symbols, pins, graph)
    gaps = detect_connectivity_gaps(symbols, pin_connectivity=pin_conn, connectivity_graph=graph)
    assert "Net-(R1-Pad1)" in gaps["auto_generated_nets"]
