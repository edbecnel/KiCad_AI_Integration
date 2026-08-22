"""Tests for singleton Assistant window."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_show_assistant_window_reuses_singleton() -> None:
    pytest.importorskip("wx")
    import wx

    from plugin.assistant_window import reset_assistant_window_for_tests, show_assistant_window

    reset_assistant_window_for_tests()
    app = wx.GetApp()
    if app is None:
        app = wx.App(False)

    parent = wx.Frame(None, title="parent")
    parent.Show(False)
    pro = FIXTURES / "testproj.kicad_pro"

    with patch("ui.launcher.present_top_level_window"):
        first = show_assistant_window(parent, pro)
        second = show_assistant_window(parent, pro)
        assert first is second

    first.Destroy()
    reset_assistant_window_for_tests()
    parent.Destroy()
