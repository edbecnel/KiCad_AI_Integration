"""Smoke tests for Audits tab."""

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


def test_audits_tab_enables_after_context_refresh() -> None:
    wx = _ensure_wx_app()
    from ui.audits_tab import AuditsTab

    frame = wx.Frame(None, title="test")
    tab = AuditsTab(frame)
    frame.Show(False)

    from context.collector import collect_stretch_context

    ctx = collect_stretch_context(FIXTURES / "testproj.kicad_pro", verbose=False)
    tab.on_context_refreshed(ctx, "summary")

    assert tab._shell is not None
    assert tab._shell._btn_schematic.IsEnabled()

    frame.Destroy()
