"""Smoke tests for in-app User Guide viewer."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
_wx_app: object | None = None


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


def test_show_user_guide_opens_frame() -> None:
    wx = _ensure_wx_app()
    from ui.help_dialog import UserGuideFrame, reset_user_guide_for_tests, show_user_guide

    reset_user_guide_for_tests()
    frame = wx.Frame(None, title="parent")
    frame.Show(False)

    shown = show_user_guide(frame, topic="README.md")
    assert isinstance(shown, UserGuideFrame)
    assert shown.IsShown()
    assert "User Guides" in shown._title.GetLabel() or shown._title.GetLabel()

    shown.load_tab_help("chat")
    assert shown._current_rel_path == "02_Chat.md"

    shown.Destroy()
    frame.Destroy()
    reset_user_guide_for_tests()


def test_assistant_shell_has_help_button() -> None:
    wx = _ensure_wx_app()
    from ui.assistant_shell import AssistantShell

    pro = FIXTURES / "testproj.kicad_pro"
    frame = wx.Frame(None, title="test")
    shell = AssistantShell(frame, initial_path=pro)
    frame.Show(False)

    assert hasattr(shell, "_btn_help")
    assert shell._btn_help.GetLabel() == "Help"

    frame.Destroy()
