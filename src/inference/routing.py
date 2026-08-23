"""Routing inference orchestration (EIE)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from context.collector import _resolve_project_file
from context.model import ProjectContext
from context.pcb_extract import collect_pcb_detail
from context.routing_checkpoint import RoutingCheckpoint, accept_routing_candidate, reject_routing_candidate
from prompts import BuiltPrompt
from prompts.templates.routing_policy import build_routing_policy_prompt
from providers import get_provider
from providers.types import ProviderResponse
from routing.factory import get_routing_engine
from routing.policy import build_exclusions_from_policy, explain_exclusion
from routing.policy_parse import parse_routing_policy_json
from routing.policy_store import load_routing_policy, save_routing_policy
from routing.types import (
    BoardReference,
    RoutingEngineCapabilities,
    RoutingExecutionOptions,
    RoutingPolicy,
    RoutingQualityReport,
    RoutingRequest,
    RoutingResult,
)
from utils.config import AppConfig, load_config


@dataclass
class RoutingPolicyResult:
    policy: RoutingPolicy
    response: ProviderResponse
    built: BuiltPrompt
    saved_path: Path | None = None


@dataclass
class RoutingPanelContext:
    project_path: Path
    capabilities: RoutingEngineCapabilities
    pcb_available: bool
    policy: RoutingPolicy
    exclusion_explanations: list[str]


def get_routing_panel_context(
    project_path: Path,
    *,
    config: AppConfig | None = None,
    policy: RoutingPolicy | None = None,
) -> RoutingPanelContext:
    """Collect routing workflow context for UI or CLI."""
    cfg = config or load_config()
    pro_path = _resolve_project_file(project_path)
    engine = get_routing_engine(cfg)
    capabilities = engine.capabilities()
    pcb_detail = collect_pcb_detail(pro_path)
    active_policy = policy or load_routing_policy(pro_path) or RoutingPolicy()
    explanations = [
        explain_exclusion(entry) for entry in active_policy.net_classifications
    ]
    return RoutingPanelContext(
        project_path=pro_path,
        capabilities=capabilities,
        pcb_available=pcb_detail is not None,
        policy=active_policy,
        exclusion_explanations=explanations,
    )


def build_routing_request(
    project_path: Path,
    *,
    policy: RoutingPolicy | None = None,
    config: AppConfig | None = None,
    timeout_sec: int | None = None,
) -> RoutingRequest:
    """Build an engine-independent routing request from project path and policy."""
    cfg = config or load_config()
    pro_path = _resolve_project_file(project_path)
    active_policy = policy or load_routing_policy(pro_path) or RoutingPolicy()
    exclusions = build_exclusions_from_policy(active_policy)
    pcb_path = pro_path.parent / f"{pro_path.stem}.kicad_pcb"
    exec_opts = RoutingExecutionOptions(
        timeout_sec=timeout_sec or cfg.routing_timeout_sec,
    )
    return RoutingRequest(
        board_reference=BoardReference(project_path=pro_path, pcb_path=pcb_path),
        routing_policy=active_policy,
        routing_exclusions=exclusions,
        execution_options=exec_opts,
    )


def run_routing(
    request: RoutingRequest,
    *,
    config: AppConfig | None = None,
) -> RoutingResult:
    """Execute routing via configured engine."""
    cfg = config or load_config()
    if not cfg.routing_enabled:
        return RoutingResult(
            success=False,
            errors=["Routing is disabled. Set routing_enabled=true in config."],
        )
    engine = get_routing_engine(cfg)
    return engine.route(request)


def _checkpoint_from_result(result: RoutingResult) -> RoutingCheckpoint:
    if result.candidate_pcb_path is None or result.original_pcb_path is None:
        raise ValueError("Routing result missing checkpoint metadata.")
    exports_dir = result.candidate_pcb_path.parent
    checkpoint_pcb = exports_dir / f"{result.checkpoint_id}.checkpoint.kicad_pcb"
    if not checkpoint_pcb.is_file():
        checkpoint_pcb = next(exports_dir.glob("*.checkpoint.kicad_pcb"), checkpoint_pcb)
    return RoutingCheckpoint(
        checkpoint_id=result.checkpoint_id or result.candidate_pcb_path.stem,
        original_pcb_path=result.original_pcb_path,
        checkpoint_pcb_path=checkpoint_pcb,
        exports_dir=exports_dir,
        created_at=result.checkpoint_id or "",
    )


def accept_routing_result(result: RoutingResult) -> Path:
    """Promote routing candidate to authoritative board."""
    checkpoint = _checkpoint_from_result(result)
    return accept_routing_candidate(checkpoint)


def reject_routing_result(result: RoutingResult) -> None:
    """Discard routing candidate."""
    checkpoint = _checkpoint_from_result(result)
    reject_routing_candidate(checkpoint)


def build_routing_quality_report(
    project_path: Path,
    *,
    result: RoutingResult | None = None,
    config: AppConfig | None = None,
) -> RoutingQualityReport:
    """Build structured post-route quality metrics from PCB extract and live DRC."""
    pro_path = _resolve_project_file(project_path)
    pcb = collect_pcb_detail(pro_path)
    report = RoutingQualityReport()
    if pcb is None:
        report.notes.append("PCB data unavailable for quality report.")
        return report

    tracks = pcb.get("tracks") or []
    vias = pcb.get("vias") or []
    report.via_count = len(vias)
    report.total_trace_length_mm = sum(
        float(t.get("length_mm") or 0) for t in tracks if isinstance(t, dict)
    )
    if result and result.routed_net_count is not None and result.unrouted_net_count is not None:
        total = result.routed_net_count + result.unrouted_net_count
        if total > 0:
            report.routed_percentage = 100.0 * result.routed_net_count / total

    from context.live.drc_runner import run_live_drc

    drc = run_live_drc(pro_path, config=config or load_config())
    if drc.get("drc_available"):
        count = int(drc.get("drc_violation_count") or 0)
        report.notes.append(f"Live DRC: {count} violation(s).")
        if count:
            for line in (drc.get("drc_violation_lines") or [])[:5]:
                report.notes.append(str(line))
    return report


def persist_routing_policy(project_path: Path | str, policy: RoutingPolicy) -> Path:
    """Save routing policy to ``kicad_ai/routing_policy.json``."""
    pro_path = _resolve_project_file(Path(project_path))
    return save_routing_policy(pro_path, policy)


def run_routing_policy_generation(
    ctx: ProjectContext,
    *,
    question: str | None = None,
    config: AppConfig | None = None,
    provider: Any | None = None,
    persist: bool = True,
) -> RoutingPolicyResult:
    """Generate routing policy via AI and optionally persist to project."""
    cfg = config or load_config()
    system, user_text = build_routing_policy_prompt(
        ctx,
        question or "Classify nets and propose exclusions for intent-aware autorouting.",
    )
    built = BuiltPrompt(
        text=user_text,
        system=system,
        template="routing_policy",
        preview_summary="Routing policy generation",
        estimated_text_tokens=max(1, len(user_text) // 4),
        include_image=False,
        image_byte_size=0,
    )
    resolved_provider = provider or get_provider(cfg)
    response = resolved_provider.send_message(
        built.text,
        system=built.system,
        config=cfg,
    )
    policy = parse_routing_policy_json(response.text)
    saved_path = persist_routing_policy(ctx.project_path, policy) if persist else None
    return RoutingPolicyResult(
        policy=policy,
        response=response,
        built=built,
        saved_path=saved_path,
    )
