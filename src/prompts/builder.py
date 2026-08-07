"""Assemble prompts from ProjectContext and named templates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from context.model import ProjectContext
from context.netlist_export import format_netlist_status_line
from platform_core.contracts import DesignSnapshot
from prompts.templates.general_review import (
    GENERAL_REVIEW_SYSTEM,
    build_general_review_sections,
    wrap_xml_sections,
)
from prompts.templates.pcb_layout import PCB_LAYOUT_SYSTEM, build_pcb_layout_sections
from prompts.templates.isolation_clearance import (
    ISOLATION_CLEARANCE_SYSTEM,
    build_isolation_clearance_sections,
)
from prompts.templates.netlist_crosscheck import (
    NETLIST_CROSSCHECK_SYSTEM,
    build_netlist_crosscheck_sections,
)
from context.context_flags import ContextIncludeFlags

TemplateName = str


@dataclass
class BuiltPrompt:
    """Prompt ready for the provider layer."""

    text: str
    system: str | None
    template: TemplateName
    preview_summary: str
    estimated_text_tokens: int
    include_image: bool = False
    image_byte_size: int = 0


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars per token) for preview display."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def build_prompt_summary(ctx: ProjectContext, *, include_image: bool = False) -> str:
    """Human-readable context summary for UI preview."""
    resolved = sum(1 for r in ctx.datasheet_resolutions.values() if r.status == "resolved")
    missing = sum(
        1 for r in ctx.datasheet_resolutions.values() if r.status in ("missing", "fetch_failed")
    )
    lines = [
        f"Project: {ctx.project_name}",
        f"Schematics: {', '.join(ctx.schematics) or '(none)'}",
        f"Symbols: {len(ctx.symbols)}",
        f"Datasheets: {resolved} resolved, {missing} missing/failed",
    ]
    labels = getattr(ctx, "schematic_connectivity", None)
    if labels and isinstance(labels, dict):
        unique = labels.get("unique_net_names") or []
        if unique:
            lines.append(f"Net labels: {len(unique)} unique names")
    lines.append(format_netlist_status_line(getattr(ctx, "netlist_summary", None)))
    pcb = getattr(ctx, "pcb_summary", None)
    if pcb and isinstance(pcb, dict):
        pcb_file = pcb.get("pcb_file")
        footprints = pcb.get("footprint_count")
        nets = pcb.get("net_count")
        if pcb_file is not None:
            lines.append(f"PCB ({pcb_file}): {footprints} footprints, {nets} nets")
    if include_image and ctx.schematic_image:
        lines.append(f"Schematic image: {len(ctx.schematic_image):,} bytes (attached separately)")
    elif include_image:
        err = getattr(ctx, "schematic_image_error", None)
        if err:
            lines.append(f"Schematic image: export failed — {err}")
        else:
            lines.append("Schematic image: requested but not exported")
    return "\n".join(lines)


def build_subckt_prompt(
    ctx: ProjectContext,
    part: str,
    *,
    tier: str | None = None,
    stage: str = "synthesis",
    facts: dict | None = None,
    datasheet_text: str = "",
    pdf_path: str | None = None,
) -> BuiltPrompt:
    """Build a SUBCKT generation prompt for one part Value."""
    from prompts.templates.subckt import build_subckt_prompt_for_tier

    part_norm = part.strip()
    sym = next(
        (
            s
            for s in ctx.symbols
            if (s.value or s.reference).strip() == part_norm
        ),
        None,
    )
    if sym is None:
        raise ValueError(f"No symbol with Value {part_norm!r}")

    res = ctx.datasheet_resolutions.get(sym.reference)
    chosen = tier or (res.tier_hint if res else "C")
    sym_ctx = {
        "reference": sym.reference,
        "value": sym.value,
        "footprint": sym.footprint,
        "lib_id": sym.lib_id,
        "datasheet": sym.datasheet,
        "spice_model": sym.spice_model,
        "spice_lib": sym.spice_lib,
        "custom_fields": sym.custom_fields,
    }
    project_ctx = {
        "project_name": ctx.project_name,
        "schematics": ctx.schematics,
    }
    user, system = build_subckt_prompt_for_tier(
        chosen,  # type: ignore[arg-type]
        part_norm,
        sym_ctx,
        datasheet_text=datasheet_text,
        pdf_path=pdf_path,
        facts=facts,
        project_context=project_ctx,
        stage=stage,  # type: ignore[arg-type]
    )
    preview = f"SUBCKT generation (Tier {chosen}) for {part_norm} ({sym.reference})"
    return BuiltPrompt(
        text=user,
        system=system,
        template=f"subckt_tier_{chosen.lower()}",
        preview_summary=preview,
        estimated_text_tokens=estimate_tokens(user),
    )


def build_general_review_prompt(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include_image: bool = False,
    include: ContextIncludeFlags | None = None,
) -> BuiltPrompt:
    """Build the general schematic design review prompt."""
    sections = build_general_review_sections(
        ctx,
        question,
        functional_description=functional_description,
        include=include,
    )
    text = wrap_xml_sections(sections)
    image_size = len(ctx.schematic_image) if include_image and ctx.schematic_image else 0
    preview = build_prompt_summary(ctx, include_image=include_image)
    est = estimate_tokens(text)
    if include_image and image_size:
        est += max(1, image_size // 800)
    return BuiltPrompt(
        text=text,
        system=GENERAL_REVIEW_SYSTEM,
        template="general_review",
        preview_summary=preview,
        estimated_text_tokens=est,
        include_image=include_image and ctx.schematic_image is not None,
        image_byte_size=image_size,
    )


def build_pcb_layout_prompt(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> BuiltPrompt:
    """Build PCB layout / trace audit prompt."""
    sections = build_pcb_layout_sections(
        ctx,
        question,
        functional_description=functional_description,
        include=include,
    )
    text = wrap_xml_sections(sections)
    preview = build_prompt_summary(ctx, include_image=False)
    est = estimate_tokens(text)
    return BuiltPrompt(
        text=text,
        system=PCB_LAYOUT_SYSTEM,
        template="pcb_layout_audit",
        preview_summary=preview,
        estimated_text_tokens=est,
    )


def build_isolation_clearance_prompt(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> BuiltPrompt:
    """Build isolation and clearance audit prompt."""
    sections = build_isolation_clearance_sections(
        ctx,
        question,
        functional_description=functional_description,
        include=include,
    )
    text = wrap_xml_sections(sections)
    preview = build_prompt_summary(ctx, include_image=False)
    est = estimate_tokens(text)
    return BuiltPrompt(
        text=text,
        system=ISOLATION_CLEARANCE_SYSTEM,
        template="isolation_clearance_audit",
        preview_summary=preview,
        estimated_text_tokens=est,
    )


def build_netlist_crosscheck_prompt(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include: ContextIncludeFlags | None = None,
) -> BuiltPrompt:
    """Build netlist vs schematic cross-check prompt."""
    sections = build_netlist_crosscheck_sections(
        ctx,
        question,
        functional_description=functional_description,
        include=include,
    )
    text = wrap_xml_sections(sections)
    preview = build_prompt_summary(ctx, include_image=False)
    est = estimate_tokens(text)
    return BuiltPrompt(
        text=text,
        system=NETLIST_CROSSCHECK_SYSTEM,
        template="netlist_crosscheck",
        preview_summary=preview,
        estimated_text_tokens=est,
    )


def build_aerf_stage_prompt(
    snapshot: DesignSnapshot,
    family_id: str,
    stage_id: int,
    *,
    prior_stages: list[dict[str, Any]] | None = None,
    ekm_sections: dict[str, Any] | None = None,
    include_image: bool = False,
) -> BuiltPrompt:
    """Build an AERF stage analysis prompt (dry-run; no provider send)."""
    from prompts.templates.aerf_stage import (
        aerf_stage_system_message,
        build_aerf_stage_sections,
    )
    from reasoning import get_family, get_stage

    stage = get_stage(stage_id)
    family = get_family(family_id)
    sections = build_aerf_stage_sections(
        snapshot,
        family_id,
        stage_id,
        prior_stages=prior_stages,
        ekm_sections=ekm_sections,
    )
    text = wrap_xml_sections(sections)
    preview_lines = [
        f"Project: {snapshot.project_name}",
        f"Circuit family: {family.label} ({family_id})",
        f"AERF stage {stage.stage_id}: {stage.title}",
        f"Prior stages: {len(prior_stages or [])}",
    ]
    image_size = 0
    if include_image:
        data = snapshot.to_dict(include_image_bytes=True)
        image_bytes = data.get("schematic_image")
        if image_bytes:
            image_size = len(image_bytes)
            preview_lines.append(f"Schematic image: {image_size:,} bytes (attached separately)")
    est = estimate_tokens(text)
    if include_image and image_size:
        est += max(1, image_size // 800)
    return BuiltPrompt(
        text=text,
        system=aerf_stage_system_message(stage_id),
        template=f"aerf_stage_{stage_id}",
        preview_summary="\n".join(preview_lines),
        estimated_text_tokens=est,
        include_image=include_image and image_size > 0,
        image_byte_size=image_size,
    )
