"""Persist and compare routing candidates (ADP-013 Phase 5)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from routing.types import RoutingPolicy, RoutingQualityReport, RoutingResult


@dataclass
class RoutingCandidateRecord:
    """One saved routing run for side-by-side comparison."""

    candidate_id: str
    checkpoint_id: str | None
    policy_notes: str = ""
    excluded_net_count: int = 0
    routed_net_count: int | None = None
    unrouted_net_count: int | None = None
    routed_percentage: float | None = None
    via_count: int | None = None
    total_trace_length_mm: float | None = None
    candidate_pcb_path: str | None = None
    quality_notes: list[str] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "checkpoint_id": self.checkpoint_id,
            "policy_notes": self.policy_notes,
            "excluded_net_count": self.excluded_net_count,
            "routed_net_count": self.routed_net_count,
            "unrouted_net_count": self.unrouted_net_count,
            "routed_percentage": self.routed_percentage,
            "via_count": self.via_count,
            "total_trace_length_mm": self.total_trace_length_mm,
            "candidate_pcb_path": self.candidate_pcb_path,
            "quality_notes": self.quality_notes,
            "created_at": self.created_at,
        }


def routing_candidates_file_path(project_path: Path | str) -> Path:
    pro = Path(project_path).expanduser().resolve()
    return pro.parent / "kicad_ai" / "routing_candidates.json"


def load_routing_candidates(project_path: Path | str) -> list[RoutingCandidateRecord]:
    path = routing_candidates_file_path(project_path)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, dict):
        return []
    raw = data.get("candidates")
    if not isinstance(raw, list):
        return []
    records: list[RoutingCandidateRecord] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        cid = item.get("candidate_id")
        if not isinstance(cid, str) or not cid:
            continue
        notes = item.get("quality_notes")
        records.append(
            RoutingCandidateRecord(
                candidate_id=cid,
                checkpoint_id=item.get("checkpoint_id")
                if isinstance(item.get("checkpoint_id"), str)
                else None,
                policy_notes=str(item.get("policy_notes") or ""),
                excluded_net_count=int(item.get("excluded_net_count") or 0),
                routed_net_count=item.get("routed_net_count"),
                unrouted_net_count=item.get("unrouted_net_count"),
                routed_percentage=item.get("routed_percentage"),
                via_count=item.get("via_count"),
                total_trace_length_mm=item.get("total_trace_length_mm"),
                candidate_pcb_path=item.get("candidate_pcb_path"),
                quality_notes=[str(n) for n in notes] if isinstance(notes, list) else [],
                created_at=str(item.get("created_at") or ""),
            )
        )
    return records


def save_routing_candidates(
    project_path: Path | str,
    candidates: list[RoutingCandidateRecord],
) -> Path:
    path = routing_candidates_file_path(project_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "candidates": [c.to_dict() for c in candidates],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def record_from_routing_run(
    result: RoutingResult,
    *,
    policy: RoutingPolicy,
    quality: RoutingQualityReport | dict[str, Any] | None = None,
) -> RoutingCandidateRecord:
    quality_dict = quality.to_dict() if isinstance(quality, RoutingQualityReport) else (quality or {})
    candidate_id = result.checkpoint_id or (
        result.candidate_pcb_path.stem if result.candidate_pcb_path else "unknown"
    )
    return RoutingCandidateRecord(
        candidate_id=candidate_id,
        checkpoint_id=result.checkpoint_id,
        policy_notes=policy.notes,
        excluded_net_count=len(policy.excluded_nets()),
        routed_net_count=result.routed_net_count,
        unrouted_net_count=result.unrouted_net_count,
        routed_percentage=quality_dict.get("routed_percentage"),
        via_count=quality_dict.get("via_count"),
        total_trace_length_mm=quality_dict.get("total_trace_length_mm"),
        candidate_pcb_path=str(result.candidate_pcb_path) if result.candidate_pcb_path else None,
        quality_notes=list(quality_dict.get("notes") or []),
        created_at=result.checkpoint_id or candidate_id,
    )


def append_routing_candidate(
    project_path: Path | str,
    record: RoutingCandidateRecord,
    *,
    max_candidates: int = 5,
) -> list[RoutingCandidateRecord]:
    candidates = load_routing_candidates(project_path)
    candidates = [c for c in candidates if c.candidate_id != record.candidate_id]
    candidates.append(record)
    candidates = candidates[-max_candidates:]
    save_routing_candidates(project_path, candidates)
    return candidates


def compare_routing_candidates(
    candidates: list[RoutingCandidateRecord],
) -> dict[str, Any]:
    """Build a side-by-side comparison summary for UI or reports."""
    if not candidates:
        return {"count": 0, "rows": [], "summary": "No routing candidates stored."}
    rows: list[dict[str, Any]] = []
    best_routed: RoutingCandidateRecord | None = None
    for cand in candidates:
        rows.append(cand.to_dict())
        if cand.routed_percentage is not None:
            if best_routed is None or (
                best_routed.routed_percentage is not None
                and cand.routed_percentage > best_routed.routed_percentage
            ):
                best_routed = cand
            elif best_routed.routed_percentage is None:
                best_routed = cand
    summary = f"{len(candidates)} candidate(s) on file."
    if best_routed is not None and best_routed.routed_percentage is not None:
        summary += (
            f" Best routed coverage: {best_routed.candidate_id} "
            f"({best_routed.routed_percentage:.1f}%)."
        )
    return {
        "count": len(candidates),
        "rows": rows,
        "best_candidate_id": best_routed.candidate_id if best_routed else None,
        "summary": summary,
        "columns": comparison_column_headers(),
        "table": comparison_table_rows(rows),
    }


def comparison_column_headers() -> list[str]:
    return [
        "Candidate",
        "Routed %",
        "Vias",
        "Excluded",
        "Policy notes",
    ]


def comparison_table_rows(rows: list[dict[str, Any]]) -> list[list[str]]:
    table: list[list[str]] = []
    for row in rows:
        routed = row.get("routed_percentage")
        table.append(
            [
                str(row.get("candidate_id") or ""),
                f"{routed:.1f}" if isinstance(routed, (int, float)) else "—",
                str(row.get("via_count") if row.get("via_count") is not None else "—"),
                str(row.get("excluded_net_count") if row.get("excluded_net_count") is not None else "0"),
                str(row.get("policy_notes") or "")[:60],
            ]
        )
    return table
