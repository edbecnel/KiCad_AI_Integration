"""PCB layout and trace audit prompt template."""

from __future__ import annotations

import json
from typing import Any

from context.context_flags import ContextIncludeFlags
from context.model import ProjectContext
from prompts.compact import compact_context_for_prompt
from prompts.templates.general_review import wrap_xml_sections

PCB_LAYOUT_SYSTEM = (
    "You are an expert PCB layout engineer reviewing a KiCad design. "
    "Use PCB track, via, zone, and net-class data when present. "
    "Flag clearance risks, return paths, high-current routes, and layer usage. "
    "Cite net names and reference designators from the context."
)


def build_pcb_layout_sections(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> dict[str, str]:
    flags = include or ContextIncludeFlags()
    sections: dict[str, str] = {}

    if functional_description and functional_description.strip():
        sections["functional_description"] = functional_description.strip()

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
        context_data["netlist_summary"] = ctx.netlist_summary

    sections["kicad_python_extracted_data"] = json.dumps(context_data, indent=2)
    sections["user_question"] = question.strip() or (
        "Review PCB layout: trace widths, critical nets, return paths, and DRC risks."
    )
    return sections


def build_pcb_layout_prompt_text(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> str:
    return wrap_xml_sections(
        build_pcb_layout_sections(
            ctx,
            question,
            functional_description=functional_description,
            include=include,
        )
    )
