"""Netlist vs schematic cross-check prompt template."""

from __future__ import annotations

import json
from typing import Any

from context.context_flags import ContextIncludeFlags
from context.model import ProjectContext
from prompts.compact import compact_context_for_prompt
from prompts.templates.general_review import wrap_xml_sections

NETLIST_CROSSCHECK_SYSTEM = (
    "You are an expert electronics design engineer performing a netlist consistency audit. "
    "Cross-reference schematic net labels, symbol instances, and SPICE netlist connectivity. "
    "Flag auto-generated net names, missing connections, and mismatches between labels and netlist nodes. "
    "Cite reference designators and net names explicitly."
)


def build_netlist_crosscheck_sections(
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
    if flags.netlist and ctx.netlist_summary:
        context_data["netlist_summary"] = {
            "export_status": ctx.netlist_summary.get("export_status"),
            "line_count": ctx.netlist_summary.get("line_count"),
            "preview_lines": ctx.netlist_summary.get("preview_lines"),
            "include_paths": ctx.netlist_summary.get("include_paths"),
        }
    if flags.netlist and ctx.connectivity_graph:
        context_data["connectivity_graph"] = ctx.connectivity_graph

    sections: dict[str, str] = {}
    if functional_description and functional_description.strip():
        sections["functional_description"] = functional_description.strip()
    sections["kicad_python_extracted_data"] = json.dumps(context_data, indent=2)
    sections["audit_focus"] = (
        "Perform a NETLIST VS SCHEMATIC audit:\n"
        "1. Verify switching devices, diodes, and critical nets in the netlist match labeled schematic nets\n"
        "2. List auto-generated nets (Net-(…)) and assess whether they hide design intent\n"
        "3. Note unconnected or suspicious pin nodes in the connectivity graph\n"
        "4. Summarize confidence and list open questions where data is insufficient"
    )
    sections["user_question"] = question.strip()
    return sections


def build_netlist_crosscheck_prompt_text(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> tuple[str, str]:
    sections = build_netlist_crosscheck_sections(
        ctx,
        question,
        functional_description=functional_description,
        include=include,
    )
    return wrap_xml_sections(sections), NETLIST_CROSSCHECK_SYSTEM
