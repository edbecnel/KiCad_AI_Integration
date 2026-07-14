"""General schematic design review template."""

from __future__ import annotations

import json
from typing import Any

from context.model import ProjectContext
from prompts.compact import compact_context_for_prompt

GENERAL_REVIEW_SYSTEM = (
    "You are an expert electronics design engineer reviewing a KiCad schematic. "
    "Use the structured project context below. Be specific about part references, "
    "net names, and datasheet coverage. Flag missing datasheets when they limit analysis."
)


def build_general_review_sections(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
) -> dict[str, str]:
    """Return XML section name → body for the general review template."""
    context_data = compact_context_for_prompt(ctx)
    sections: dict[str, str] = {}

    if functional_description and functional_description.strip():
        sections["functional_description"] = functional_description.strip()

    sections["kicad_python_extracted_data"] = json.dumps(
        context_data,
        indent=2,
    )

    netlist = context_data.get("schematic_connectivity")
    if netlist:
        sections["kicad_netlist"] = json.dumps(netlist, indent=2)

    sections["user_question"] = question.strip()
    return sections


def wrap_xml_sections(sections: dict[str, str]) -> str:
    """Wrap section bodies in XML-style tags."""
    parts: list[str] = []
    for name, body in sections.items():
        parts.append(f"<{name}>\n{body}\n</{name}>")
    return "\n\n".join(parts)
