"""Netlist connectivity gap-fill inference prompt template."""

from __future__ import annotations

import json
from typing import Any

from context.context_flags import ContextIncludeFlags
from context.model import ProjectContext
from prompts.compact import compact_context_for_prompt
from prompts.templates.general_review import wrap_xml_sections

NETLIST_GAP_FILL_SYSTEM = (
    "You are an expert electronics design engineer inferring missing schematic connectivity. "
    "Given partial net labels, symbol pin lists, and SPICE netlist fragments, propose "
    "pin-to-net assignments for unconnected pins and explain auto-generated net names. "
    "Output structured JSON only — never claim certainty without evidence."
)


def build_netlist_gap_fill_sections(
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
        context_data["schematic_connectivity"] = data.get("schematic_connectivity")
    if flags.netlist and ctx.netlist_summary:
        context_data["netlist_summary"] = {
            "export_status": ctx.netlist_summary.get("export_status"),
            "preview_lines": ctx.netlist_summary.get("preview_lines"),
        }
    if flags.netlist and ctx.connectivity_graph:
        context_data["connectivity_graph"] = ctx.connectivity_graph
    if ctx.connectivity_gaps:
        context_data["connectivity_gaps"] = ctx.connectivity_gaps

    sections: dict[str, str] = {}
    if functional_description and functional_description.strip():
        sections["functional_description"] = functional_description.strip()
    sections["kicad_python_extracted_data"] = json.dumps(context_data, indent=2)
    sections["gap_fill_task"] = (
        "Perform CONNECTIVITY GAP-FILL inference:\n"
        "1. List unconnected pins and auto-generated nets (Net-(…)) from the context\n"
        "2. Propose likely pin-to-net assignments with confidence and evidence\n"
        "3. Flag items that require human verification or ERC before trusting\n"
        "4. Return JSON: {\"inferred_connections\": [...], \"open_questions\": [...], "
        "\"confidence\": \"low|medium|high\"}"
    )
    sections["user_question"] = question.strip()
    return sections


def build_netlist_gap_fill_prompt(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> tuple[str, str]:
    sections = build_netlist_gap_fill_sections(
        ctx,
        question,
        functional_description=functional_description,
        include=include,
    )
    return wrap_xml_sections(sections), NETLIST_GAP_FILL_SYSTEM
