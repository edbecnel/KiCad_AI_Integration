"""Tests for selection and firmware live helpers."""

from __future__ import annotations

import sys
from pathlib import Path

from context.live.firmware import load_firmware_summary, project_settings_path
from context.live.selection import collect_selection_context


def test_collect_selection_context_no_board() -> None:
    result = collect_selection_context()
    assert result["available"] is False
    assert result["footprints"] == []


def test_collect_selection_context_with_selection(monkeypatch) -> None:
    class _Fp:
        def GetReference(self) -> str:
            return "R1"

        def GetValue(self) -> str:
            return "10k"

    class _Board:
        def GetCurrentSelection(self):
            return [_Fp()]

    class _Pcbnew:
        @staticmethod
        def GetBoard():
            return _Board()

    monkeypatch.setitem(sys.modules, "pcbnew", _Pcbnew)
    result = collect_selection_context()
    assert result["available"] is True
    assert result["footprints"][0]["reference"] == "R1"


def test_load_firmware_summary_missing_file(tmp_path: Path) -> None:
    result = load_firmware_summary(tmp_path / "missing.py")
    assert result is not None
    assert result["available"] is False


def test_load_firmware_summary_truncates_large_file(tmp_path: Path) -> None:
    path = tmp_path / "big.py"
    path.write_bytes(b"x" * 40_000)
    result = load_firmware_summary(path)
    assert result is not None
    assert result["available"] is True
    assert result["truncated"] is True


def test_project_settings_path(blocking_oscillator_pro: Path) -> None:
    path = project_settings_path(blocking_oscillator_pro)
    assert path.name == "settings.json"
    assert path.parent.name == "kicad_ai"
