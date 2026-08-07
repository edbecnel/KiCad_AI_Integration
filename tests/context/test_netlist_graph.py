"""Tests for SPICE netlist connectivity graph parsing."""

from context.netlist_graph import build_connectivity_graph

SAMPLE_NETLIST = """
.title KiCad schematic
.include "models.lib"
R1 VCC Net-(R1-Pad1) 10k
R2 Net-(R1-Pad1) GND 4.7k
XQ1 COLLECTOR BASE EMITTER BD243C
.end
"""


def test_build_connectivity_graph_passives_and_subckt() -> None:
    graph = build_connectivity_graph(SAMPLE_NETLIST)
    assert graph is not None
    assert "VCC" in graph["nets"]
    assert "GND" in graph["nets"]
    assert graph["connection_count"] >= 6
    assert any(c["reference"] == "XQ1" and c.get("subckt") == "BD243C" for c in graph["connections"])
    assert graph["auto_generated_nets"]
    assert graph["include_paths"] == ["models.lib"]


def test_build_connectivity_graph_empty() -> None:
    assert build_connectivity_graph("") is None
    assert build_connectivity_graph(".title only\n.end") is None
