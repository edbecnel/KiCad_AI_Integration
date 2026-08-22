"""Tests for KiCad project path resolution from open board."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _ensure_wx_app():
    pytest.importorskip("wx")
    import wx

    global _wx_app
    if wx.GetApp() is None:
        try:
            _wx_app = wx.App(False)
        except SystemExit:
            pytest.skip("wx display not available")
    return wx


_wx_app: object | None = None


def _pcbnew_with_board(filename: str | None) -> types.ModuleType:
    class _Board:
        def GetFileName(self) -> str:
            return filename or ""

    pcbnew = types.ModuleType("pcbnew")
    pcbnew.GetBoard = lambda: _Board() if filename is not None else None
    return pcbnew


def test_try_resolve_project_pro_path_none_without_board() -> None:
    pcbnew = _pcbnew_with_board(None)
    with patch.dict(sys.modules, {"pcbnew": pcbnew}):
        from ui.launcher import try_resolve_project_pro_path

        assert try_resolve_project_pro_path(None) is None


def test_try_resolve_project_pro_path_none_with_unsaved_board() -> None:
    pcbnew = _pcbnew_with_board("")
    with patch.dict(sys.modules, {"pcbnew": pcbnew}):
        from ui.launcher import try_resolve_project_pro_path

        assert try_resolve_project_pro_path(None) is None


def test_try_resolve_project_pro_path_none_from_open_board(tmp_path: Path) -> None:
    pro = tmp_path / "myproj.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    pcb_path = tmp_path / "myproj.kicad_pcb"
    pcb_path.write_text("", encoding="utf-8")

    pcbnew = _pcbnew_with_board(str(pcb_path))
    with patch.dict(sys.modules, {"pcbnew": pcbnew}):
        from ui.launcher import try_resolve_project_pro_path

        assert try_resolve_project_pro_path(None) == pro.resolve()


def test_try_resolve_project_pro_path_explicit_file() -> None:
    from ui.launcher import try_resolve_project_pro_path

    pro = FIXTURES / "testproj.kicad_pro"
    assert try_resolve_project_pro_path(pro) == pro.resolve()


def test_try_resolve_project_pro_path_explicit_invalid_returns_none() -> None:
    from ui.launcher import try_resolve_project_pro_path

    assert try_resolve_project_pro_path("/nonexistent/project.kicad_pro") is None


def test_effective_initial_project_path_auto_detects_when_omitted(tmp_path: Path) -> None:
    pro = tmp_path / "myproj.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    pcb_path = tmp_path / "myproj.kicad_pcb"
    pcb_path.write_text("", encoding="utf-8")

    pcbnew = _pcbnew_with_board(str(pcb_path))
    with patch.dict(sys.modules, {"pcbnew": pcbnew}):
        from ui.launcher import effective_initial_project_path

        assert effective_initial_project_path(None) == pro.resolve()


def test_effective_initial_project_path_keeps_explicit_path() -> None:
    from ui.launcher import effective_initial_project_path

    explicit = FIXTURES / "testproj.kicad_pro"
    assert effective_initial_project_path(explicit) == explicit


def test_assistant_shell_auto_fills_project_from_open_board(tmp_path: Path) -> None:
    pytest.importorskip("wx")

    pro = tmp_path / "myproj.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    pcb_path = tmp_path / "myproj.kicad_pcb"
    pcb_path.write_text("", encoding="utf-8")

    pcbnew = _pcbnew_with_board(str(pcb_path))

    wx = _ensure_wx_app()

    with patch.dict(sys.modules, {"pcbnew": pcbnew}):
        from ui.assistant_shell import AssistantShell

        frame = wx.Frame(None, title="test")
        shell = AssistantShell(frame, initial_path=None)
        assert shell._txt_path.GetValue() == str(pro.resolve())
        assert shell._summary.GetValue()
        frame.Destroy()
