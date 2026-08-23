"""Export routing policy learning candidates (ADP-012, not auto-canonical)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from routing.types import RoutingPolicy
from utils.config import AppConfig, load_config


@dataclass(frozen=True)
class RoutingLearningExportResult:
    exported: bool
    path: Path | None
    message: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def routing_learning_dir(project_path: Path | str, *, config: AppConfig | None = None) -> Path:
    cfg = config or load_config()
    pro = Path(project_path).expanduser().resolve()
    subdir = cfg.learning_library_subdir.strip() or "learning"
    return pro.parent / "kicad_ai" / subdir / "routing_policies"


def export_routing_policy_candidate(
    project_path: Path | str,
    policy: RoutingPolicy,
    *,
    quality_summary: dict[str, Any] | None = None,
    accepted: bool = False,
    config: AppConfig | None = None,
) -> RoutingLearningExportResult:
    """
    Write a routing-policy learning candidate for human review.

    Does not auto-promote to canonical knowledge (ADP-012 gate).
    """
    pro = Path(project_path).expanduser().resolve()
    out_dir = routing_learning_dir(pro, config=config)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"routing_policy_{stamp}.json"
    payload = {
        "exported_at": _utc_now_iso(),
        "project_path": str(pro),
        "accepted_to_board": accepted,
        "policy": policy.to_dict(),
        "quality_summary": quality_summary or {},
        "review_status": "candidate",
        "note": "Human review required before treating as canonical routing guidance.",
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return RoutingLearningExportResult(
        exported=True,
        path=path,
        message=f"Routing policy learning candidate saved: {path}",
    )
