"""Routing inference orchestration (EIE)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from context.collector import _resolve_project_file
from context.pcb_extract import collect_pcb_detail
from context.routing_checkpoint import RoutingCheckpoint, accept_routing_candidate, reject_routing_candidate
from routing.factory import get_routing_engine
from routing.policy import build_exclusions_from_policy, explain_exclusion
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
    active_policy = policy or RoutingPolicy()
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
    active_policy = policy or RoutingPolicy()
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
