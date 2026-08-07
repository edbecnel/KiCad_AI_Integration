"""Tests for audit prompt templates."""

from __future__ import annotations

from context.model import ProjectContext
from prompts import (
    build_isolation_clearance_prompt,
    build_netlist_crosscheck_prompt,
    build_pcb_layout_prompt,
)


def _ctx() -> ProjectContext:
    return ProjectContext(
        project_path="/tmp/p",
        project_name="demo",
        schematic_connectivity={"unique_net_names": ["VCC", "GND"]},
        connectivity_graph={
            "nets": ["VCC", "GND"],
            "connections": [{"reference": "R1", "pin": "1", "net": "VCC"}],
            "connection_count": 1,
            "auto_generated_nets": [],
            "include_paths": [],
        },
    )


def test_isolation_clearance_prompt_sections() -> None:
    built = build_isolation_clearance_prompt(_ctx(), "Check HV isolation.")
    assert built.template == "isolation_clearance_audit"
    assert "<audit_focus>" in built.text
    assert "connectivity_graph" in built.text


def test_netlist_crosscheck_prompt_sections() -> None:
    built = build_netlist_crosscheck_prompt(_ctx(), "Cross-check netlist.")
    assert built.template == "netlist_crosscheck"
    assert "<audit_focus>" in built.text
    assert "NETLIST VS SCHEMATIC" in built.text


def test_pcb_layout_prompt_sections() -> None:
    built = build_pcb_layout_prompt(_ctx(), "Review traces.")
    assert built.template == "pcb_layout_audit"
    assert "<user_question>" in built.text
