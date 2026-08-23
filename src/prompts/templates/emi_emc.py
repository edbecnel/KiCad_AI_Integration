"""EMI/EMC audit prompt template."""

from __future__ import annotations

import json
from typing import Any

from context.context_flags import ContextIncludeFlags
from context.model import ProjectContext
from prompts.compact import compact_context_for_prompt
from prompts.templates.general_review import wrap_xml_sections

EMI_EMC_SYSTEM = (
    "You are an expert EMI/EMC and PCB layout engineer. Review switching loop area, "
    "filtering, shielding, ground partitioning, edge rates, and isolation gaps. "
    "Cite nets and components from the provided context."
)


def build_emi_emc_sections(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> dict[str, str]:
    flags = include or ContextIncludeFlags(pcb=True, schematic=True)
    context_data: dict[str, Any] = {}
    if flags.schematic:
        data = compact_context_for_prompt(ctx)
        context_data["symbols"] = data.get("symbols")
        context_data["schematic_connectivity"] = data.get("schematic_connectivity")
    if flags.pcb and ctx.pcb_summary:
        context_data["pcb_summary"] = ctx.pcb_summary
    if flags.erc_drc and ctx.erc_drc_summary:
        context_data["erc_drc_summary"] = ctx.erc_drc_summary

    sections: dict[str, str] = {}
    if functional_description and functional_description.strip():
        sections["functional_description"] = functional_description.strip()
    sections["kicad_python_extracted_data"] = json.dumps(context_data, indent=2)
    sections["audit_focus"] = (
        "Perform an EMI/EMC-oriented review focused on:\n"
        "1. Minimizing high di/dt loop area on switching power paths\n"
        "2. Filtering and snubbing on inductive switching nodes\n"
        "3. Ground/reference partitioning between analog, digital, and power\n"
        "4. Antenna-like structures, long unterminated traces, and slot emissions"
    )
    sections["user_question"] = question.strip()
    return sections


def build_emi_emc_prompt_text(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> tuple[str, str]:
    sections = build_emi_emc_sections(
        ctx, question, functional_description=functional_description, include=include
    )
    return wrap_xml_sections(sections), EMI_EMC_SYSTEM
