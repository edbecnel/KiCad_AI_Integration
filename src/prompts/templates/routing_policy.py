"""Routing policy generation prompt (Phase 4)."""

from __future__ import annotations

import json
from typing import Any

from context.context_flags import ContextIncludeFlags
from context.model import ProjectContext
from prompts.compact import compact_context_for_prompt
from prompts.templates.general_review import wrap_xml_sections

ROUTING_POLICY_SYSTEM = (
    "You are an expert PCB layout engineer assisting with routing policy. "
    "Classify nets for intent-aware autorouting: identify critical nets that must "
    "be excluded from bulk autorouting, high-current paths, differential pairs, "
    "clock lines, analog-sensitive signals, and ordinary signals safe for delegation. "
    "Return structured JSON with net_classifications array. Each entry must include "
    "net_name, classification, and explain (why this net was classified). "
    "Do not route everything automatically — preserve engineering intent."
)


def build_routing_policy_sections(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> dict[str, str]:
    flags = include or ContextIncludeFlags(pcb=True, schematic=True)
    sections: dict[str, str] = {}

    if functional_description and functional_description.strip():
        sections["functional_description"] = functional_description.strip()

    context_data: dict[str, Any] = {}
    if flags.schematic:
        data = compact_context_for_prompt(ctx)
        context_data["project_name"] = data.get("project_name")
        context_data["symbols"] = data.get("symbols")
        context_data["schematic_connectivity"] = data.get("schematic_connectivity")
    if flags.pcb and ctx.pcb_summary:
        context_data["pcb_summary"] = ctx.pcb_summary
    if flags.netlist and ctx.netlist_summary:
        context_data["netlist_summary"] = ctx.netlist_summary

    sections["kicad_python_extracted_data"] = json.dumps(context_data, indent=2)
    sections["user_question"] = question.strip() or (
        "Analyze this board and propose a routing policy with net classifications "
        "and exclusions for intent-aware autorouting."
    )
    sections["output_format"] = json.dumps(
        {
            "net_classifications": [
                {
                    "net_name": "MOTOR_OUT",
                    "classification": "high_current",
                    "explain": "Expected 18–20 A; requires wide copper.",
                }
            ],
            "notes": "Optional routing strategy notes.",
        },
        indent=2,
    )
    return sections


def build_routing_policy_prompt(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> tuple[str, str]:
    sections = build_routing_policy_sections(
        ctx,
        question,
        functional_description=functional_description,
        include=include,
    )
    user_prompt = wrap_xml_sections(sections)
    return ROUTING_POLICY_SYSTEM, user_prompt
