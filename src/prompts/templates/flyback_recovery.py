"""Flyback recovery / Bedini-style audit prompt template."""

from __future__ import annotations

import json
from typing import Any

from context.context_flags import ContextIncludeFlags
from context.model import ProjectContext
from prompts.compact import compact_context_for_prompt
from prompts.templates.general_review import wrap_xml_sections

FLYBACK_RECOVERY_SYSTEM = (
    "You are an expert power electronics engineer reviewing flyback recovery, "
    "blocking-oscillator, and Bedini-style radiant energy circuits. Focus on "
    "isolation between control logic and high-voltage switching, flyback diode "
    "stress, coil/trifilar magnetics, and netlist vs schematic consistency. "
    "Cite reference designators and net names such as HV_Flyback, Coil_Plus, "
    "and GPIO isolation paths when present."
)

DEFAULT_FLYBACK_QUESTION = (
    "Review this flyback recovery / blocking oscillator design for isolation, "
    "switching path integrity, component stress, and netlist consistency."
)


def build_flyback_recovery_sections(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> dict[str, str]:
    flags = include or ContextIncludeFlags(
        schematic=True, pcb=True, bom=True, netlist=True, erc_drc=True
    )
    context_data: dict[str, Any] = {}
    if flags.schematic:
        data = compact_context_for_prompt(ctx)
        context_data["project_name"] = data.get("project_name")
        context_data["symbols"] = data.get("symbols")
        context_data["schematic_connectivity"] = data.get("schematic_connectivity")
    if flags.pcb and ctx.pcb_summary:
        context_data["pcb_summary"] = ctx.pcb_summary
    if flags.bom and ctx.bom_summary:
        context_data["bom_summary"] = ctx.bom_summary
    if flags.netlist and ctx.netlist_summary:
        context_data["netlist_summary"] = {
            "export_status": ctx.netlist_summary.get("export_status"),
            "preview_lines": ctx.netlist_summary.get("preview_lines"),
        }
    if flags.erc_drc and ctx.erc_drc_summary:
        context_data["erc_drc_summary"] = ctx.erc_drc_summary
    if ctx.firmware_summary:
        context_data["firmware_summary"] = ctx.firmware_summary

    sections: dict[str, str] = {}
    if functional_description and functional_description.strip():
        sections["functional_description"] = functional_description.strip()
    sections["kicad_python_extracted_data"] = json.dumps(context_data, indent=2)
    sections["audit_focus"] = (
        "Flyback recovery audit checklist:\n"
        "1. Optocoupler or driver isolation between MCU/GPIO and HV switching\n"
        "2. Flyback diode and switching transistor Vds/transient stress\n"
        "3. Labeled HV nets (e.g. HV_Flyback, Coil_Plus) vs netlist connectivity\n"
        "4. Creepage/clearance and trace capacity on high-current paths\n"
        "5. Firmware timing vs netlist if firmware context is provided"
    )
    sections["user_question"] = question.strip() or DEFAULT_FLYBACK_QUESTION
    return sections


def build_flyback_recovery_prompt_text(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> tuple[str, str]:
    sections = build_flyback_recovery_sections(
        ctx,
        question or DEFAULT_FLYBACK_QUESTION,
        functional_description=functional_description,
        include=include,
    )
    return wrap_xml_sections(sections), FLYBACK_RECOVERY_SYSTEM
