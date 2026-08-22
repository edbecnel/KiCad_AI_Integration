"""AERF orchestration — dry-run bundles, approval-gated send, multi-stage pipeline."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from ekm.aerf_writeback import AERFWritebackPlan, plan_aerf_writeback, write_aerf_stages_to_ekm

from platform_core.contracts import DesignSnapshot
from prompts import BuiltPrompt, build_aerf_stage_prompt
from providers import get_provider
from providers.types import ProviderResponse
from reasoning import AERF_STAGE_COUNT, classify_circuit_family, load_stage_excerpt
from reasoning.classifier import FamilyClassification
from reasoning.stage_schemas import validate_stage_envelope
from reasoning.stages import AERFStage, get_stage
from utils.config import AppConfig, load_config

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
_REQUIRED_ENVELOPE_KEYS = ("stage_id", "determinations")
AERF_PROVIDER_MAX_TOKENS = 8192
_AERF_TRUNCATION_RETRY_SUFFIX = (
    "\n\nYour previous response was truncated or invalid JSON. "
    "Reply with ONLY a complete valid JSON object matching aerf_output_schema. "
    "Be concise; use only schema keys; limit lists to 6 items."
)


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


AERFStage0Bundle = AERFStageBundle


@dataclass
class AERFSendResult:
    """Provider response for one AERF stage after explicit send."""

    response: ProviderResponse
    built: BuiltPrompt
    family_id: str
    stage_id: int
    parsed: dict[str, Any] | None
    parse_error: str | None


@dataclass
class AERFStageRunResult:
    """One stage build (and optional send) in a pipeline."""

    plan: AERFStagePlan
    built: BuiltPrompt
    send: AERFSendResult | None = None


@dataclass
class AERFPipelineResult:
    """Multi-stage AERF run with accumulated prior stage outputs."""

    family_id: str
    stage_runs: list[AERFStageRunResult]
    completed_stages: list[dict[str, Any]]
    failed_at_stage: int | None = None
    parse_error: str | None = None


def _resolve_aerf_config(
    cfg: AppConfig,
    *,
    api_key_override: str | None = None,
) -> AppConfig:
    """Raise output token budget for AERF stage JSON envelopes."""
    max_tokens = max(cfg.provider_max_tokens, AERF_PROVIDER_MAX_TOKENS)
    key_override = (api_key_override or "").strip()
    key = key_override or cfg.anthropic_api_key
    if max_tokens == cfg.provider_max_tokens and not key_override:
        return cfg
    return AppConfig(
        artifact_library_path=cfg.artifact_library_path,
        datasheet_search_paths=cfg.datasheet_search_paths,
        schematic_image_dpi=cfg.schematic_image_dpi,
        datasheet_url_fetch=cfg.datasheet_url_fetch,
        url_fetch_timeout_sec=cfg.url_fetch_timeout_sec,
        url_fetch_read_timeout_sec=cfg.url_fetch_read_timeout_sec,
        url_fetch_warmup=cfg.url_fetch_warmup,
        kicad_cli=cfg.kicad_cli,
        anthropic_api_key=key,
        ai_provider=cfg.ai_provider,
        claude_model=cfg.claude_model,
        provider_timeout_sec=cfg.provider_timeout_sec,
        provider_read_timeout_sec=cfg.provider_read_timeout_sec,
        provider_max_tokens=max_tokens,
        datasheet_ai_discovery=cfg.datasheet_ai_discovery,
        datasheet_ai_discovery_auto_fetch=cfg.datasheet_ai_discovery_auto_fetch,
        datasheet_ai_discovery_max_urls=cfg.datasheet_ai_discovery_max_urls,
        datasheet_reset_quarantine_local_pdf=cfg.datasheet_reset_quarantine_local_pdf,
        datasheet_write_symbol_url=cfg.datasheet_write_symbol_url,
        spice_write_symbol_fields=cfg.spice_write_symbol_fields,
        learning_auto_promote=cfg.learning_auto_promote,
        learning_min_confidence=cfg.learning_min_confidence,
        learning_library_subdir=cfg.learning_library_subdir,
    )


def _resolve_ekm_for_aerf(
    snapshot: DesignSnapshot,
    ekm_sections: dict[str, Any] | None,
    ekm_family_id: str | None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Auto-load project EKM for AERF when caller did not supply sections."""
    if ekm_sections is not None and ekm_family_id is not None:
        return ekm_sections, ekm_family_id
    project_path = getattr(snapshot, "project_path", None)
    if not project_path:
        return ekm_sections, ekm_family_id
    from ekm.prompt_context import load_ekm_prompt_bundle

    bundle = load_ekm_prompt_bundle(project_path)
    sections = ekm_sections if ekm_sections is not None else (bundle.sections or None)
    family_id = ekm_family_id or bundle.family_id
    return sections, family_id


def _snapshot_image(snapshot: DesignSnapshot, *, include_image: bool) -> bytes | None:
    if not include_image:
        return None
    direct = getattr(snapshot, "schematic_image", None)
    if isinstance(direct, bytes) and direct:
        return direct
    data = snapshot.to_dict(include_image_bytes=True)
    raw = data.get("schematic_image")
    return raw if isinstance(raw, bytes) and raw else None


def _extract_json_text(text: str) -> str:
    stripped = text.strip()
    match = _JSON_FENCE_RE.search(stripped)
    if match:
        return match.group(1).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end > start:
        return stripped[start : end + 1]
    return stripped


def parse_stage_output(
    text: str,
    *,
    expected_stage_id: int | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Parse AERF stage JSON envelope from provider text."""
    try:
        payload = json.loads(_extract_json_text(text))
    except json.JSONDecodeError as exc:
        return None, f"JSON decode error: {exc}"

    if not isinstance(payload, dict):
        return None, "Stage output must be a JSON object"

    missing = [key for key in _REQUIRED_ENVELOPE_KEYS if key not in payload]
    if missing:
        return None, f"Missing required keys: {', '.join(missing)}"

    stage_id = payload.get("stage_id")
    if not isinstance(stage_id, int):
        return None, "stage_id must be an integer"

    if expected_stage_id is not None and stage_id != expected_stage_id:
        return None, f"stage_id {stage_id} does not match expected {expected_stage_id}"

    if not isinstance(payload.get("determinations"), dict):
        return None, "determinations must be an object"

    for key in ("open_questions", "unknowns"):
        if key in payload and not isinstance(payload[key], list):
            return None, f"{key} must be a list when present"

    return validate_stage_envelope(payload, expected_stage_id=expected_stage_id)


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
    config: AppConfig | None = None,
) -> tuple[FamilyClassification, AERFStagePlan]:
    cfg = config or load_config()
    classification = classify_circuit_family(
        snapshot,
        user_hint=user_hint,
        ekm_family_id=ekm_family_id,
        config=cfg,
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
    classification: FamilyClassification | None = None
    resolved_family = family_id
    if resolved_family is None:
        classification, _plan = classify_and_plan(
            snapshot,
            stage_id=0,
            user_hint=user_hint,
            ekm_family_id=ekm_family_id,
            config=load_config(),
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


def send_aerf_stage_prompt(
    built: BuiltPrompt,
    snapshot: DesignSnapshot,
    *,
    family_id: str,
    stage_id: int,
    config: AppConfig | None = None,
    api_key_override: str | None = None,
    provider: Any | None = None,
) -> AERFSendResult:
    """Send a built AERF prompt — caller must have approved transmission."""
    cfg = _resolve_aerf_config(config or load_config(), api_key_override=api_key_override)
    llm = provider if provider is not None else get_provider(cfg)
    image = _snapshot_image(snapshot, include_image=built.include_image)
    response = llm.send_message(
        built.text,
        system=built.system,
        image=image,
        config=cfg,
    )
    parsed, parse_error = parse_stage_output(response.text, expected_stage_id=stage_id)
    if parse_error and (
        response.stop_reason == "max_tokens"
        or parse_error.startswith("JSON decode error")
    ):
        retry_response = llm.send_message(
            built.text + _AERF_TRUNCATION_RETRY_SUFFIX,
            system=built.system,
            image=image,
            config=cfg,
        )
        retry_parsed, retry_error = parse_stage_output(
            retry_response.text,
            expected_stage_id=stage_id,
        )
        if retry_parsed is not None:
            response = retry_response
            parsed, parse_error = retry_parsed, retry_error
        elif retry_error and retry_response.stop_reason != "max_tokens":
            response = retry_response
            parsed, parse_error = retry_parsed, retry_error
    return AERFSendResult(
        response=response,
        built=built,
        family_id=family_id,
        stage_id=stage_id,
        parsed=parsed,
        parse_error=parse_error,
    )


def run_aerf_stage(
    snapshot: DesignSnapshot,
    family_id: str,
    stage_id: int,
    *,
    prior_stages: list[dict[str, Any]] | None = None,
    ekm_sections: dict[str, Any] | None = None,
    include_image: bool = False,
    approve_send: bool = False,
    config: AppConfig | None = None,
    api_key_override: str | None = None,
    provider: Any | None = None,
) -> AERFStageRunResult:
    """Build one stage prompt; send only when ``approve_send`` is True."""
    plan, built = build_aerf_stage_prompt_bundle(
        snapshot,
        family_id,
        stage_id,
        prior_stages=prior_stages,
        ekm_sections=ekm_sections,
        include_image=include_image,
    )
    send_result: AERFSendResult | None = None
    if approve_send:
        send_result = send_aerf_stage_prompt(
            built,
            snapshot,
            family_id=family_id,
            stage_id=stage_id,
            config=config,
            api_key_override=api_key_override,
            provider=provider,
        )
    return AERFStageRunResult(plan=plan, built=built, send=send_result)


def run_aerf_pipeline(
    snapshot: DesignSnapshot,
    *,
    family_id: str | None = None,
    stages: Sequence[int] | None = None,
    prior_stages: list[dict[str, Any]] | None = None,
    user_hint: str | None = None,
    ekm_family_id: str | None = None,
    ekm_sections: dict[str, Any] | None = None,
    include_image: bool = False,
    approve_send: bool = False,
    stop_on_parse_error: bool = True,
    stop_after_stage: int | None = None,
    config: AppConfig | None = None,
    api_key_override: str | None = None,
    provider: Any | None = None,
) -> AERFPipelineResult:
    """Run AERF stages sequentially; accumulate parsed outputs in ``completed_stages``."""
    ekm_sections, loaded_ekm_family = _resolve_ekm_for_aerf(
        snapshot,
        ekm_sections,
        ekm_family_id,
    )
    if ekm_family_id is None:
        ekm_family_id = loaded_ekm_family

    resolved_family = family_id
    if resolved_family is None:
        classification = classify_circuit_family(
            snapshot,
            user_hint=user_hint,
            ekm_family_id=ekm_family_id,
            config=config or load_config(),
        )
        resolved_family = classification.family_id

    stage_ids = list(stages) if stages is not None else list(range(AERF_STAGE_COUNT))
    completed = list(prior_stages or [])
    runs: list[AERFStageRunResult] = []
    failed_at: int | None = None
    parse_error: str | None = None

    for stage_id in stage_ids:
        if stop_after_stage is not None and stage_id > stop_after_stage:
            break

        run = run_aerf_stage(
            snapshot,
            resolved_family,
            stage_id,
            prior_stages=completed,
            ekm_sections=ekm_sections,
            include_image=include_image,
            approve_send=approve_send,
            config=config,
            api_key_override=api_key_override,
            provider=provider,
        )
        runs.append(run)

        if not approve_send or run.send is None:
            continue

        if run.send.parse_error:
            failed_at = stage_id
            parse_error = run.send.parse_error
            if stop_on_parse_error:
                break
        elif run.send.parsed is not None:
            completed.append(run.send.parsed)

    return AERFPipelineResult(
        family_id=resolved_family,
        stage_runs=runs,
        completed_stages=completed,
        failed_at_stage=failed_at,
        parse_error=parse_error,
    )


@dataclass
class AERFPipelineWritebackResult:
    """AERF pipeline run with optional EKM write-back."""

    pipeline: AERFPipelineResult
    writeback_plan: AERFWritebackPlan
    ekm_path: Path | None = None
    promotion_message: str | None = None
    promoted_family_id: str | None = None


def build_ekm_writeback_plan(pipeline_result: AERFPipelineResult) -> AERFWritebackPlan:
    """Build an EKM write-back plan from completed AERF stage envelopes."""
    return plan_aerf_writeback(pipeline_result.completed_stages)


def run_aerf_pipeline_and_writeback(
    snapshot: DesignSnapshot,
    project_path: Path | str,
    *,
    family_id: str | None = None,
    stages: Sequence[int] | None = None,
    prior_stages: list[dict[str, Any]] | None = None,
    user_hint: str | None = None,
    ekm_family_id: str | None = None,
    ekm_sections: dict[str, Any] | None = None,
    include_image: bool = False,
    approve_send: bool = False,
    approve_ekm_writeback: bool = False,
    stop_on_parse_error: bool = True,
    stop_after_stage: int | None = None,
    config: AppConfig | None = None,
    api_key_override: str | None = None,
    provider: Any | None = None,
) -> AERFPipelineWritebackResult:
    """Run the AERF pipeline; persist to EKM only when ``approve_ekm_writeback`` is True."""
    pipeline = run_aerf_pipeline(
        snapshot,
        family_id=family_id,
        stages=stages,
        prior_stages=prior_stages,
        user_hint=user_hint,
        ekm_family_id=ekm_family_id,
        ekm_sections=ekm_sections,
        include_image=include_image,
        approve_send=approve_send,
        stop_on_parse_error=stop_on_parse_error,
        stop_after_stage=stop_after_stage,
        config=config,
        api_key_override=api_key_override,
        provider=provider,
    )
    writeback_plan, ekm_path = write_aerf_stages_to_ekm(
        project_path,
        pipeline.completed_stages,
        approve=approve_ekm_writeback,
    )
    promotion_message: str | None = None
    promoted_family_id: str | None = None
    if approve_ekm_writeback and pipeline.failed_at_stage is None and pipeline.completed_stages:
        from learning.family_promotion import try_auto_promote

        promo = try_auto_promote(
            pipeline.completed_stages,
            snapshot,
            project_path,
            config=config or load_config(),
        )
        promotion_message = promo.message
        promoted_family_id = promo.family_id if promo.promoted else None

    return AERFPipelineWritebackResult(
        pipeline=pipeline,
        writeback_plan=writeback_plan,
        ekm_path=ekm_path,
        promotion_message=promotion_message,
        promoted_family_id=promoted_family_id,
    )
