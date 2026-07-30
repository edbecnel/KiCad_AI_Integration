"""AERF orchestration (dry-run bundles and prompt assembly; no auto cloud send)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_core.contracts import DesignSnapshot
from prompts import BuiltPrompt, build_aerf_stage_prompt
from reasoning import classify_circuit_family, load_stage_excerpt
from reasoning.classifier import FamilyClassification
from reasoning.stages import AERFStage, get_stage


@dataclass
class AERFStagePlan:
    family_id: str
    stage: AERFStage
    kb_excerpt_path: str
    kb_excerpt_chars: int
    design_snapshot_keys: list[str] = field(default_factory=list)


@dataclass
class AERFStageBundle:
    """Dry-run context for one AERF stage."""

    family_id: str
    classification: FamilyClassification | None
    stage_plan: AERFStagePlan
    kb_excerpt_preview: str
    design_summary: dict[str, Any]


# Backward-compatible alias
AERFStage0Bundle = AERFStageBundle


def plan_stage(
    family_id: str,
    stage_id: int,
    snapshot: DesignSnapshot,
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


def classify_and_plan(
    snapshot: DesignSnapshot,
    stage_id: int = 0,
    *,
    user_hint: str | None = None,
    ekm_family_id: str | None = None,
) -> tuple[FamilyClassification, AERFStagePlan]:
    classification = classify_circuit_family(
        snapshot,
        user_hint=user_hint,
        ekm_family_id=ekm_family_id,
    )
    plan = plan_stage(classification.family_id, stage_id, snapshot)
    return classification, plan


def build_stage_bundle(
    snapshot: DesignSnapshot,
    family_id: str,
    stage_id: int,
    *,
    preview_chars: int = 500,
    classification: FamilyClassification | None = None,
) -> AERFStageBundle:
    """Build a dry-run bundle for one AERF stage without invoking an LLM."""
    excerpt = load_stage_excerpt(family_id, stage_id)
    plan = plan_stage(family_id, stage_id, snapshot)
    preview = excerpt.content[:preview_chars]
    if len(excerpt.content) > preview_chars:
        preview += "\n…"
    return AERFStageBundle(
        family_id=family_id,
        classification=classification,
        stage_plan=plan,
        kb_excerpt_preview=preview,
        design_summary={
            "project_path": snapshot.project_path,
            "project_name": snapshot.project_name,
        },
    )


def build_stage0_bundle(
    snapshot: DesignSnapshot,
    family_id: str | None = None,
    *,
    preview_chars: int = 500,
    user_hint: str | None = None,
    ekm_family_id: str | None = None,
) -> AERFStageBundle:
    """Build stage-0 dry-run bundle; classifies family when ``family_id`` is omitted."""
    classification: FamilyClassification | None = None
    resolved_family = family_id
    if resolved_family is None:
        classification, _plan = classify_and_plan(
            snapshot,
            stage_id=0,
            user_hint=user_hint,
            ekm_family_id=ekm_family_id,
        )
        resolved_family = classification.family_id
    return build_stage_bundle(
        snapshot,
        resolved_family,
        0,
        preview_chars=preview_chars,
        classification=classification,
    )


def build_aerf_stage_prompt_bundle(
    snapshot: DesignSnapshot,
    family_id: str,
    stage_id: int,
    *,
    prior_stages: list[dict[str, Any]] | None = None,
    ekm_sections: dict[str, Any] | None = None,
    include_image: bool = False,
) -> tuple[AERFStagePlan, BuiltPrompt]:
    """Build stage plan and prompt — dry-run only; caller must approve before send."""
    plan = plan_stage(family_id, stage_id, snapshot)
    built = build_aerf_stage_prompt(
        snapshot,
        family_id,
        stage_id,
        prior_stages=prior_stages,
        ekm_sections=ekm_sections,
        include_image=include_image,
    )
    return plan, built
