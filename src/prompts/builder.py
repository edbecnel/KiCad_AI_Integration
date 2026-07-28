"""Assemble prompts from ProjectContext and named templates."""

from __future__ import annotations

from dataclasses import dataclass

from context.model import ProjectContext
from prompts.templates.general_review import (
    GENERAL_REVIEW_SYSTEM,
    build_general_review_sections,
    wrap_xml_sections,
)

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
) -> BuiltPrompt:
    """Build the general schematic design review prompt."""
    sections = build_general_review_sections(
        ctx,
        question,
        functional_description=functional_description,
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
