"""Post-route review prompt (Phase 4)."""

from __future__ import annotations

import json
from typing import Any

from context.context_flags import ContextIncludeFlags
from context.model import ProjectContext
from prompts.compact import compact_context_for_prompt
from prompts.templates.general_review import wrap_xml_sections

POST_ROUTE_REVIEW_SYSTEM = (
    "You are an expert PCB layout engineer reviewing autorouted copper. "
    "Evaluate routing quality: DRC risks, unrouted nets, via count, trace length, "
    "layer transitions, critical-net violations, high-current bottlenecks, "
    "differential-pair integrity, return paths, and manufacturability. "
    "Assume the board was routed by an external autorouter — do not assume the "
    "result is acceptable without engineering review. Cite net names from context."
)


def build_post_route_review_sections(
    ctx: ProjectContext,
    question: str,
    *,
    routing_result_summary: dict[str, Any] | None = None,
    quality_report: dict[str, Any] | None = None,
    include: ContextIncludeFlags | None = None,
) -> dict[str, str]:
    flags = include or ContextIncludeFlags(pcb=True, erc_drc=True)
    sections: dict[str, str] = {}

    context_data: dict[str, Any] = {}
    if flags.pcb and ctx.pcb_summary:
        context_data["pcb_summary"] = ctx.pcb_summary
    if flags.erc_drc and ctx.erc_drc_summary:
        context_data["erc_drc_summary"] = ctx.erc_drc_summary

    sections["kicad_python_extracted_data"] = json.dumps(context_data, indent=2)

    if routing_result_summary:
        sections["routing_result"] = json.dumps(routing_result_summary, indent=2)
    if quality_report:
        sections["routing_quality_report"] = json.dumps(quality_report, indent=2)

    sections["user_question"] = question.strip() or (
        "Review the autorouted board. Identify routing quality concerns and "
        "whether the result should be accepted, revised, or rejected."
    )
    return sections


def build_post_route_review_prompt(
    ctx: ProjectContext,
    question: str,
    *,
    routing_result_summary: dict[str, Any] | None = None,
    quality_report: dict[str, Any] | None = None,
    include: ContextIncludeFlags | None = None,
) -> tuple[str, str]:
    sections = build_post_route_review_sections(
        ctx,
        question,
        routing_result_summary=routing_result_summary,
        quality_report=quality_report,
        include=include,
    )
    user_prompt = wrap_xml_sections(sections)
    return POST_ROUTE_REVIEW_SYSTEM, user_prompt
