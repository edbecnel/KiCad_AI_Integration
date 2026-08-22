"""Tests for project path helpers (no wx required)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ui.project_path import normalize_launcher_project_path

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_normalize_launcher_project_path_accepts_kicad_pro() -> None:
    pro = FIXTURES / "testproj.kicad_pro"
    assert normalize_launcher_project_path(str(pro)) == pro.resolve()


def test_normalize_launcher_project_path_accepts_directory() -> None:
    pro = normalize_launcher_project_path(str(FIXTURES))
    assert pro.suffix == ".kicad_pro"
    assert pro.parent == FIXTURES.resolve()


def test_normalize_launcher_project_path_rejects_empty() -> None:
    with pytest.raises(ValueError, match="Select a KiCad project"):
        normalize_launcher_project_path("   ")
