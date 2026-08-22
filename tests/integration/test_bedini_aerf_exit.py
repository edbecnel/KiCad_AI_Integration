"""Blocking oscillator / AERF exit criteria integration tests (repo fixtures)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from context.collector import collect_stretch_context
from context.context_flags import ContextIncludeFlags
from inference.aerf import build_ekm_writeback_plan, run_aerf_pipeline
from inference.chat import build_chat_prompt
from providers.types import ProviderResponse, TokenUsage
from reasoning.stage_schemas import STAGE_DETERMINATION_KEYS
from utils.config import AppConfig

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
OSCILLATOR_PRO = FIXTURES / "blocking_oscillator.kicad_pro"

_STAGE_FROM_SYSTEM = re.compile(r"Stage (\d+) —")


def _stage_id_from_call(prompt: str, system: str | None) -> int:
    """Resolve active AERF stage from system message (not prior_stages in prompt)."""
    if system:
        match = _STAGE_FROM_SYSTEM.search(system)
        if match:
            return int(match.group(1))
    for stage_id in range(7, -1, -1):
        marker = f'"stage_id": {stage_id}'
        aerf_idx = prompt.find("<aerf_stage>")
        if aerf_idx >= 0 and marker in prompt[aerf_idx:]:
            return stage_id
    return 0


def _mock_determinations(stage_id: int) -> str:
    keys = STAGE_DETERMINATION_KEYS.get(stage_id, ())
    samples = {
        "family_id": '"blocking_oscillator"',
        "family_label": '"Blocking Oscillator"',
        "topology": '"blocking"',
        "functional_blocks": "[]",
        "inputs": "[]",
        "outputs": "[]",
        "operating_sequence": "[]",
        "startup_behavior": '"unknown"',
        "control_mechanism": '"unknown"',
        "energy_source": '"DC"',
        "storage_elements": "[]",
        "transfer_path": '"primary"',
        "governing_equations": "[]",
        "components": "[]",
        "modes": "[]",
        "mechanical_interactions": "null",
        "thermal_effects": "null",
        "environmental_influences": "null",
        "external_systems": "[]",
        "performance_evaluation": '"pending"',
        "failure_analysis": "[]",
        "optimization_suggestions": "[]",
        "measurement_recommendations": "[]",
        "design_improvements": "[]",
        "conclusions": "[]",
    }
    parts = [f'"{k}": {samples.get(k, "[]")}' for k in keys]
    return "{" + ", ".join(parts) + "}"


class _BediniMockProvider:
    def send_message(self, prompt: str, *, system=None, image=None, config=None, **kwargs):
        stage_id = _stage_id_from_call(prompt, system)
        body = (
            f'{{"stage_id": {stage_id}, "stage_key": "test", "title": "T", '
            f'"question": "Q", "determinations": {_mock_determinations(stage_id)}, '
            f'"open_questions": [], "confidence": "high", "unknowns": []}}'
        )
        return ProviderResponse(text=body, model="mock", usage=TokenUsage(1, 1))


@pytest.fixture
def oscillator_config(tmp_path: Path) -> AppConfig:
    return AppConfig(artifact_library_path=tmp_path / "library")


def test_bedini_collect_context(oscillator_config: AppConfig) -> None:
    ctx = collect_stretch_context(OSCILLATOR_PRO, config=oscillator_config, verbose=False)
    assert ctx.project_name == "blocking_oscillator"
    assert len(ctx.symbols) > 0
    assert ctx.bom_summary is not None
    assert len(ctx.bom_summary) > 0


def test_bedini_aerf_pipeline_dry_run(oscillator_config: AppConfig) -> None:
    ctx = collect_stretch_context(OSCILLATOR_PRO, config=oscillator_config, verbose=False)
    result = run_aerf_pipeline(ctx, approve_send=False)
    assert result.family_id == "blocking_oscillator"
    assert len(result.stage_runs) == 8


def test_bedini_aerf_exit_mock_pipeline_and_writeback(oscillator_config: AppConfig) -> None:
    ctx = collect_stretch_context(OSCILLATOR_PRO, config=oscillator_config, verbose=False)
    provider = _BediniMockProvider()
    result = run_aerf_pipeline(
        ctx,
        approve_send=True,
        provider=provider,
    )
    assert result.failed_at_stage is None
    assert len(result.completed_stages) == 8
    plan = build_ekm_writeback_plan(result)
    assert plan.stage_count == 8
    assert "circuit_overview" in plan.section_ids


def test_bedini_chat_smoke_build_prompt(oscillator_config: AppConfig) -> None:
    """Chat smoke: build general_review prompt from fixture context (no provider call)."""
    ctx = collect_stretch_context(OSCILLATOR_PRO, config=oscillator_config, verbose=False)
    built = build_chat_prompt(
        ctx,
        "Summarize the blocking oscillator topology and key components.",
        include=ContextIncludeFlags(bom=True, erc_drc=True),
    )
    assert built.template == "general_review"
    assert len(built.text) > 200
    assert "blocking" in built.text.lower() or "oscillator" in built.text.lower()
