"""Isolation and clearance audit prompt template."""

from __future__ import annotations

import json
from typing import Any

from context.context_flags import ContextIncludeFlags
from context.model import ProjectContext
from prompts.compact import compact_context_for_prompt
from prompts.templates.general_review import wrap_xml_sections

ISOLATION_CLEARANCE_SYSTEM = (
    "You are an expert power electronics and embedded systems hardware engineer. "
    "Review isolation boundaries, creepage/clearance, high-voltage switching paths, "
    "and optocoupler or driver separation between control logic and power stages. "
    "Use schematic labels, netlist connectivity, and PCB data when present. "
    "Cite reference designators and net names from the context."
)


def build_isolation_clearance_sections(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> dict[str, str]:
    flags = include or ContextIncludeFlags()
    context_data: dict[str, Any] = {}
    if flags.schematic:
        data = compact_context_for_prompt(ctx)
        context_data["project_name"] = data.get("project_name")
        context_data["symbols"] = data.get("symbols")
        context_data["symbol_count"] = data.get("symbol_count")
        context_data["schematic_connectivity"] = data.get("schematic_connectivity")
    if flags.pcb and ctx.pcb_summary:
        context_data["pcb_summary"] = ctx.pcb_summary
    if flags.bom and ctx.bom_summary:
        context_data["bom_summary"] = ctx.bom_summary
    if flags.erc_drc and ctx.erc_drc_summary:
        context_data["erc_drc_summary"] = ctx.erc_drc_summary
    if flags.netlist and ctx.netlist_summary:
        context_data["netlist_summary"] = {
            "export_status": ctx.netlist_summary.get("export_status"),
            "line_count": ctx.netlist_summary.get("line_count"),
            "preview_lines": ctx.netlist_summary.get("preview_lines"),
        }
    if flags.netlist and ctx.connectivity_graph:
        context_data["connectivity_graph"] = ctx.connectivity_graph

    sections: dict[str, str] = {}
    if functional_description and functional_description.strip():
        sections["functional_description"] = functional_description.strip()
    sections["kicad_python_extracted_data"] = json.dumps(context_data, indent=2)
    sections["audit_focus"] = (
        "Perform a critical review focused on:\n"
        "1. Isolation between control logic (e.g. MCU/GPIO) and high-voltage or inductive switching loops\n"
        "2. Creepage/clearance and return-path risks on the PCB when layout data is present\n"
        "3. Component stress on switching devices under repetitive high-voltage transients\n"
        "4. Contradictions between labeled nets and exported netlist connectivity"
    )
    sections["user_question"] = question.strip()
    return sections


def build_isolation_clearance_prompt_text(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> tuple[str, str]:
    sections = build_isolation_clearance_sections(
        ctx,
        question,
        functional_description=functional_description,
        include=include,
    )
    return wrap_xml_sections(sections), ISOLATION_CLEARANCE_SYSTEM
