"""Signal integrity audit prompt template."""

from __future__ import annotations

import json
from typing import Any

from context.context_flags import ContextIncludeFlags
from context.model import ProjectContext
from prompts.compact import compact_context_for_prompt
from prompts.templates.general_review import wrap_xml_sections

SIGNAL_INTEGRITY_SYSTEM = (
    "You are an expert signal-integrity engineer. Review controlled impedance, "
    "differential pairs, return paths, via transitions, length matching, and "
    "crosstalk risks. Use schematic, netlist, and PCB data when present."
)


def build_signal_integrity_sections(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> dict[str, str]:
    flags = include or ContextIncludeFlags(pcb=True, schematic=True, netlist=True)
    context_data: dict[str, Any] = {}
    if flags.schematic:
        data = compact_context_for_prompt(ctx)
        context_data["symbols"] = data.get("symbols")
        context_data["schematic_connectivity"] = data.get("schematic_connectivity")
    if flags.pcb and ctx.pcb_summary:
        context_data["pcb_summary"] = ctx.pcb_summary
    if flags.netlist and ctx.netlist_summary:
        context_data["netlist_summary"] = ctx.netlist_summary
    if flags.netlist and ctx.connectivity_graph:
        context_data["connectivity_graph"] = ctx.connectivity_graph

    sections: dict[str, str] = {}
    if functional_description and functional_description.strip():
        sections["functional_description"] = functional_description.strip()
    sections["kicad_python_extracted_data"] = json.dumps(context_data, indent=2)
    sections["audit_focus"] = (
        "Perform a signal-integrity review focused on:\n"
        "1. High-speed or clock nets and expected impedance control\n"
        "2. Differential pair routing and length matching risks\n"
        "3. Return path discontinuities and via stub concerns\n"
        "4. Crosstalk between adjacent nets or buses"
    )
    sections["user_question"] = question.strip()
    return sections


def build_signal_integrity_prompt_text(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> tuple[str, str]:
    sections = build_signal_integrity_sections(
        ctx, question, functional_description=functional_description, include=include
    )
    return wrap_xml_sections(sections), SIGNAL_INTEGRITY_SYSTEM
