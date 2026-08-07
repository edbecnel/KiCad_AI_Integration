"""Tests for AERF stage output validation."""

from __future__ import annotations

from reasoning.stage_schemas import validate_stage_envelope


def test_validate_stage_envelope_stage0_requires_keys() -> None:
    payload = {
        "stage_id": 0,
        "determinations": {"topology": "blocking"},
        "confidence": "high",
    }
    parsed, err = validate_stage_envelope(payload, expected_stage_id=0)
    assert parsed is None
    assert err and "missing required keys" in err


def test_validate_stage_envelope_stage0_valid() -> None:
    payload = {
        "stage_id": 0,
        "determinations": {
            "family_id": "blocking_oscillator",
            "family_label": "Blocking Oscillator",
            "topology": "blocking",
            "functional_blocks": [],
            "inputs": [],
            "outputs": [],
        },
        "open_questions": [],
        "unknowns": [],
        "confidence": "medium",
    }
    parsed, err = validate_stage_envelope(payload, expected_stage_id=0)
    assert err is None
    assert parsed is not None


def test_validate_stage_envelope_bad_confidence() -> None:
    payload = {
        "stage_id": 0,
        "determinations": {
            "family_id": "x",
            "family_label": "x",
            "topology": "x",
            "functional_blocks": [],
            "inputs": [],
            "outputs": [],
        },
        "confidence": "very_high",
    }
    parsed, err = validate_stage_envelope(payload, expected_stage_id=0)
    assert parsed is None
    assert err and "confidence" in err
