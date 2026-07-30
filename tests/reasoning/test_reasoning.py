"""Tests for AERF reasoning registry and KB loader."""

from __future__ import annotations

import pytest

from reasoning import (
    AERF_STAGE_COUNT,
    STAGES,
    get_stage,
    load_families,
    load_stage_excerpt,
)
from reasoning.kb_loader import KBLoadError


def test_stage_count() -> None:
    assert AERF_STAGE_COUNT == 8
    assert len(STAGES) == 8


def test_fixed_stage_titles() -> None:
    assert get_stage(0).title == "Circuit Identification"
    assert get_stage(7).title == "Engineering Analysis"


def test_blocking_oscillator_stage_00() -> None:
    excerpt = load_stage_excerpt("blocking_oscillator", 0)
    assert "Circuit Identification" in excerpt.content
    assert excerpt.path.name.startswith("00")


def test_missing_stage_raises() -> None:
    with pytest.raises(KeyError):
        load_stage_excerpt("blocking_oscillator", 99)


def test_families_manifest() -> None:
    families = load_families()
    ids = {f.family_id for f in families}
    assert "blocking_oscillator" in ids
