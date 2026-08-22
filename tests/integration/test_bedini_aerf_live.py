"""Live AERF validation artifacts and optional API regression hook."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from context.collector import collect_stretch_context
from ekm.aerf_writeback import plan_aerf_writeback
from inference.aerf import run_aerf_stage
from reasoning.stage_schemas import validate_stage_envelope

BEDINI_PRO = Path(
    "/Users/edbecnel/Development/Local/Bedini_Self_Oscillator/Bedini_SSG_Radiant_Oscillator.kicad_pro"
)
LIVE_STAGES_FIXTURE = (
    Path(__file__).resolve().parent.parent / "fixtures" / "bedini_aerf_live" / "stages_0-7.json"
)


def _load_live_stages() -> list[dict]:
    data = json.loads(LIVE_STAGES_FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    return data


def test_bedini_aerf_live_fixture_all_stages_validate() -> None:
    """Regression anchor: captured live Bedini stage envelopes pass schema validation."""
    stages = _load_live_stages()
    assert len(stages) == 8
    for envelope in stages:
        stage_id = envelope["stage_id"]
        parsed, err = validate_stage_envelope(envelope, expected_stage_id=stage_id)
        assert err is None, f"stage {stage_id}: {err}"
        assert parsed is not None


def test_bedini_aerf_live_fixture_writeback_plan() -> None:
    stages = _load_live_stages()
    plan = plan_aerf_writeback(stages)
    assert plan.stage_count == 8
    assert plan.has_stage_7
    assert "circuit_overview" in plan.section_ids
    assert len(plan.field_plans) > 0


def test_bedini_aerf_live_fixture_stage0_bedini_signals() -> None:
    """Rubric smoke: Stage 0 names blocking oscillator family and Bedini-specific parts."""
    stage0 = _load_live_stages()[0]
    det = stage0["determinations"]
    assert det["family_id"] == "blocking_oscillator"
    blob = json.dumps(det).lower()
    assert "trifilar" in blob or "bd243" in blob
    assert "blocking" in blob or "bedini" in blob


@pytest.mark.live
@pytest.mark.skipif(not BEDINI_PRO.is_file(), reason="Local Bedini project not present")
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="Set ANTHROPIC_API_KEY to run live AERF API regression",
)
def test_bedini_aerf_live_stage0_api_smoke() -> None:
    """Optional live API smoke — not run in default CI."""
    ctx = collect_stretch_context(BEDINI_PRO, verbose=False)
    run = run_aerf_stage(ctx, "blocking_oscillator", 0, approve_send=True)
    send = run.send
    assert send is not None
    assert send.parse_error is None
    assert send.parsed is not None
    assert send.parsed["determinations"]["family_id"] == "blocking_oscillator"
