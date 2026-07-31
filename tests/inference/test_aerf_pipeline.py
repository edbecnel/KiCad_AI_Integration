"""Tests for AERF multi-stage pipeline and approval-gated send."""

from __future__ import annotations

from context.model import ProjectContext
from inference.aerf import (
    build_aerf_stage_prompt_bundle,
    build_ekm_writeback_plan,
    parse_stage_output,
    run_aerf_pipeline,
    run_aerf_stage,
    send_aerf_stage_prompt,
)
from providers.types import ProviderResponse, TokenUsage


class _MockAERFProvider:
    def __init__(self, responses: dict[int, str] | None = None) -> None:
        self.calls: list[str] = []
        self._responses = responses or {}

    def send_message(self, prompt: str, *, system=None, image=None, config=None, **kwargs):
        self.calls.append(prompt)
        for stage_id, text in self._responses.items():
            if f'"stage_id": {stage_id}' in prompt or f'"stage_id":{stage_id}' in prompt:
                return ProviderResponse(text=text, model="mock", usage=TokenUsage(1, 1))
        stage_id = 0
        if '"stage_id": 1' in prompt or "aerf_stage_1" in (system or ""):
            stage_id = 1
        elif '"stage_id": 2' in prompt:
            stage_id = 2
        text = self._responses.get(
            stage_id,
            (
                f'{{"stage_id": {stage_id}, "stage_key": "test", "title": "T", '
                f'"question": "Q", "determinations": {{}}, "open_questions": [], '
                f'"confidence": "high", "unknowns": []}}'
            ),
        )
        return ProviderResponse(text=text, model="mock", usage=TokenUsage(1, 1))


def _ctx() -> ProjectContext:
    return ProjectContext(project_path="/tmp/p", project_name="demo")


def test_parse_stage_output_valid() -> None:
    text = """Here is the analysis:
```json
{"stage_id": 0, "determinations": {"family_id": "blocking_oscillator"}, "open_questions": [], "unknowns": [], "confidence": "high"}
```"""
    parsed, err = parse_stage_output(text, expected_stage_id=0)
    assert err is None
    assert parsed is not None
    assert parsed["stage_id"] == 0


def test_parse_stage_output_wrong_stage() -> None:
    parsed, err = parse_stage_output('{"stage_id": 1, "determinations": {}}', expected_stage_id=0)
    assert parsed is None
    assert err and "does not match" in err


def test_run_aerf_stage_does_not_send_without_approval() -> None:
    provider = _MockAERFProvider()
    result = run_aerf_stage(
        _ctx(),
        "blocking_oscillator",
        0,
        approve_send=False,
        provider=provider,
    )
    assert result.built.template == "aerf_stage_0"
    assert result.send is None
    assert provider.calls == []


def test_send_aerf_stage_prompt_parses_response() -> None:
    provider = _MockAERFProvider(
        {
            0: (
                '{"stage_id": 0, "determinations": {"topology": "blocking"}, '
                '"open_questions": [], "unknowns": [], "confidence": "medium"}'
            ),
        }
    )
    ctx = _ctx()
    _plan, built = build_aerf_stage_prompt_bundle(ctx, "blocking_oscillator", 0)
    send = send_aerf_stage_prompt(
        built,
        ctx,
        family_id="blocking_oscillator",
        stage_id=0,
        provider=provider,
    )
    assert send.parsed is not None
    assert send.parse_error is None
    assert send.parsed["determinations"]["topology"] == "blocking"
    assert len(provider.calls) == 1


def test_pipeline_accumulates_prior_stages_in_prompt() -> None:
    ctx = _ctx()
    prior = [{"stage_id": 0, "determinations": {"family_id": "blocking_oscillator"}}]
    _plan, built = build_aerf_stage_prompt_bundle(
        ctx,
        "blocking_oscillator",
        2,
        prior_stages=prior,
    )
    assert '"stage_id": 0' in built.text


def test_run_aerf_pipeline_with_mock_provider() -> None:
    provider = _MockAERFProvider()
    result = run_aerf_pipeline(
        _ctx(),
        family_id="blocking_oscillator",
        stages=[0, 1],
        approve_send=True,
        provider=provider,
        stop_after_stage=1,
    )
    assert result.family_id == "blocking_oscillator"
    assert len(result.stage_runs) == 2
    assert len(result.completed_stages) == 2
    assert result.failed_at_stage is None
    assert len(provider.calls) == 2
    _plan, built = build_aerf_stage_prompt_bundle(
        _ctx(),
        "blocking_oscillator",
        1,
        prior_stages=result.completed_stages[:1],
    )
    assert '"stage_id": 0' in built.text


def test_pipeline_stops_on_parse_error() -> None:
    provider = _MockAERFProvider({0: "not json at all"})
    result = run_aerf_pipeline(
        _ctx(),
        family_id="blocking_oscillator",
        stages=[0, 1],
        approve_send=True,
        provider=provider,
        stop_on_parse_error=True,
    )
    assert result.failed_at_stage == 0
    assert result.parse_error is not None
    assert len(result.stage_runs) == 1
    assert result.completed_stages == []


def test_build_ekm_writeback_plan_from_pipeline() -> None:
    provider = _MockAERFProvider()
    result = run_aerf_pipeline(
        _ctx(),
        family_id="blocking_oscillator",
        stages=[0, 1],
        approve_send=True,
        provider=provider,
    )
    plan = build_ekm_writeback_plan(result)
    assert plan.stage_count == 2
    assert "circuit_overview" in plan.section_ids
    assert "operation_and_principles" in plan.section_ids
