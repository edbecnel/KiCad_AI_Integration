"""One-click engineering audit workflows (Phase 3)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from context.model import ProjectContext
from context.review_report import (
    STRUCTURED_FINDINGS_SUFFIX,
    ReviewReport,
    parse_findings_from_response,
    save_review_report,
)
from inference.chat import build_chat_prompt
from prompts import BuiltPrompt
from providers import get_provider
from providers.types import ProviderResponse
from utils.config import AppConfig, load_config

AUDIT_QUESTIONS = {
    "schematic_review": (
        "Perform a structured schematic design review. Highlight datasheet gaps, "
        "connectivity risks, and component selection concerns."
    ),
    "pcb_layout_review": (
        "Perform a structured PCB layout review. Comment on placement, routing, "
        "clearance, and DRC-related risks."
    ),
    "drc_interpretation": (
        "Explain the ERC/DRC results in engineering terms. Prioritize actionable fixes."
    ),
    "isolation_clearance": (
        "Review isolation and clearance for high-voltage or mixed-signal boundaries."
    ),
    "circuit_explanation": (
        "Walk through the circuit topology and explain how major functional blocks interact."
    ),
}


@dataclass
class AuditResult:
    report: ReviewReport
    response: ProviderResponse
    built: BuiltPrompt
    report_path: Path | None = None


def _resolve_config(config: AppConfig | None, api_key_override: str | None) -> AppConfig:
    cfg = config or load_config()
    if api_key_override and api_key_override.strip():
        return replace(cfg, anthropic_api_key=api_key_override.strip())
    return cfg


def _run_audit(
    audit_type: str,
    template: str,
    ctx: ProjectContext,
    *,
    question: str | None = None,
    config: AppConfig | None = None,
    api_key_override: str | None = None,
    provider: Any | None = None,
    include_image: bool = False,
    persist: bool = True,
) -> AuditResult:
    cfg = _resolve_config(config, api_key_override)
    built = build_chat_prompt(
        ctx,
        question or AUDIT_QUESTIONS.get(audit_type, "Review this design."),
        include_image=include_image,
        template=template,
    )
    built = BuiltPrompt(
        text=built.text + STRUCTURED_FINDINGS_SUFFIX,
        system=built.system,
        template=built.template,
        preview_summary=built.preview_summary,
        estimated_text_tokens=built.estimated_text_tokens,
        include_image=built.include_image,
        image_byte_size=built.image_byte_size,
    )
    resolved_provider = provider or get_provider(cfg)
    response = resolved_provider.send_message(
        built.text,
        system=built.system,
        image=ctx.schematic_image if built.include_image else None,
        config=cfg,
    )
    findings = parse_findings_from_response(response.text)
    report = ReviewReport(
        audit_type=audit_type,
        project_path=ctx.project_path,
        model=response.model,
        findings=findings,
        narrative=response.text,
        usage=response.usage,
    )
    report_path = save_review_report(report) if persist else None
    return AuditResult(report=report, response=response, built=built, report_path=report_path)


def run_schematic_review(
    ctx: ProjectContext,
    *,
    config: AppConfig | None = None,
    api_key_override: str | None = None,
    provider: Any | None = None,
    include_image: bool = False,
    persist: bool = True,
) -> AuditResult:
    return _run_audit(
        "schematic_review",
        "general_review",
        ctx,
        config=config,
        api_key_override=api_key_override,
        provider=provider,
        include_image=include_image,
        persist=persist,
    )


def run_pcb_layout_review(
    ctx: ProjectContext,
    *,
    config: AppConfig | None = None,
    api_key_override: str | None = None,
    provider: Any | None = None,
    persist: bool = True,
) -> AuditResult:
    return _run_audit(
        "pcb_layout_review",
        "pcb_layout_audit",
        ctx,
        config=config,
        api_key_override=api_key_override,
        provider=provider,
        persist=persist,
    )


def run_drc_interpretation(
    ctx: ProjectContext,
    *,
    config: AppConfig | None = None,
    api_key_override: str | None = None,
    provider: Any | None = None,
    persist: bool = True,
) -> AuditResult:
    return _run_audit(
        "drc_interpretation",
        "general_review",
        ctx,
        config=config,
        api_key_override=api_key_override,
        provider=provider,
        persist=persist,
    )


def run_isolation_clearance_audit(
    ctx: ProjectContext,
    *,
    config: AppConfig | None = None,
    api_key_override: str | None = None,
    provider: Any | None = None,
    persist: bool = True,
) -> AuditResult:
    return _run_audit(
        "isolation_clearance",
        "isolation_clearance_audit",
        ctx,
        config=config,
        api_key_override=api_key_override,
        provider=provider,
        persist=persist,
    )


def run_circuit_explanation(
    ctx: ProjectContext,
    *,
    config: AppConfig | None = None,
    api_key_override: str | None = None,
    provider: Any | None = None,
    persist: bool = True,
) -> AuditResult:
    return _run_audit(
        "circuit_explanation",
        "general_review",
        ctx,
        config=config,
        api_key_override=api_key_override,
        provider=provider,
        persist=persist,
    )
