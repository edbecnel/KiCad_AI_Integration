"""Power integrity audit prompt template."""

from __future__ import annotations

import json
from typing import Any

from context.context_flags import ContextIncludeFlags
from context.model import ProjectContext
from prompts.compact import compact_context_for_prompt
from prompts.templates.general_review import wrap_xml_sections

POWER_INTEGRITY_SYSTEM = (
    "You are an expert power-delivery and PCB power-integrity engineer. "
    "Review decoupling, bulk capacitance, return paths, plane usage, net classes, "
    "and high di/dt switching paths. Use schematic, BOM, PCB summary, and DRC data "
    "when present. Cite reference designators and net names."
)


def build_power_integrity_sections(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> dict[str, str]:
    flags = include or ContextIncludeFlags(pcb=True, schematic=True, bom=True)
    context_data: dict[str, Any] = {}
    if flags.schematic:
        data = compact_context_for_prompt(ctx)
        context_data["symbols"] = data.get("symbols")
        context_data["schematic_connectivity"] = data.get("schematic_connectivity")
    if flags.pcb and ctx.pcb_summary:
        context_data["pcb_summary"] = ctx.pcb_summary
    if flags.bom and ctx.bom_summary:
        context_data["bom_summary"] = ctx.bom_summary
    if flags.erc_drc and ctx.erc_drc_summary:
        context_data["erc_drc_summary"] = ctx.erc_drc_summary
    if getattr(ctx, "live_context", None) and ctx.live_context.get("board_settings"):
        context_data["board_settings"] = ctx.live_context["board_settings"]

    sections: dict[str, str] = {}
    if functional_description and functional_description.strip():
        sections["functional_description"] = functional_description.strip()
    sections["kicad_python_extracted_data"] = json.dumps(context_data, indent=2)
    sections["audit_focus"] = (
        "Perform a power-integrity review focused on:\n"
        "1. Decoupling placement and bulk vs ceramic strategy per rail\n"
        "2. High di/dt return paths and plane continuity\n"
        "3. Net class widths/clearances vs expected current\n"
        "4. Missing or weak PDN elements visible from schematic/PCB context"
    )
    sections["user_question"] = question.strip()
    return sections


def build_power_integrity_prompt_text(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> tuple[str, str]:
    sections = build_power_integrity_sections(
        ctx, question, functional_description=functional_description, include=include
    )
    return wrap_xml_sections(sections), POWER_INTEGRITY_SYSTEM
