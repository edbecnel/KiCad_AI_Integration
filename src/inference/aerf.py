"""AERF orchestration stub (stage-0 dry-run, no cloud send)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from reasoning import load_stage_excerpt
from reasoning.stages import AERFStage, get_stage


@runtime_checkable
class DesignSnapshotLike(Protocol):
    project_path: str
    project_name: str

    def to_dict(self, *, include_image_bytes: bool = False) -> dict[str, Any]: ...


@dataclass
class AERFStagePlan:
    family_id: str
    stage: AERFStage
    kb_excerpt_path: str
    kb_excerpt_chars: int
    design_snapshot_keys: list[str] = field(default_factory=list)


@dataclass
class AERFStage0Bundle:
    """Dry-run context for stage 0 — prompt assembly deferred to ADP-007."""

    family_id: str
    stage_plan: AERFStagePlan
    kb_excerpt_preview: str
    design_summary: dict[str, Any]


def plan_stage(
    family_id: str,
    stage_id: int,
    snapshot: DesignSnapshotLike,
) -> AERFStagePlan:
    stage = get_stage(stage_id)
    excerpt = load_stage_excerpt(family_id, stage_id)
    return AERFStagePlan(
        family_id=family_id,
        stage=stage,
        kb_excerpt_path=str(excerpt.path),
        kb_excerpt_chars=len(excerpt.content),
        design_snapshot_keys=sorted(snapshot.to_dict().keys()),
    )


def build_stage0_bundle(
    snapshot: DesignSnapshotLike,
    family_id: str,
    *,
    preview_chars: int = 500,
) -> AERFStage0Bundle:
    """Build stage-0 dry-run bundle without invoking an LLM."""
    excerpt = load_stage_excerpt(family_id, 0)
    plan = plan_stage(family_id, 0, snapshot)
    preview = excerpt.content[:preview_chars]
    if len(excerpt.content) > preview_chars:
        preview += "\n…"
    return AERFStage0Bundle(
        family_id=family_id,
        stage_plan=plan,
        kb_excerpt_preview=preview,
        design_summary={
            "project_path": snapshot.project_path,
            "project_name": snapshot.project_name,
        },
    )
