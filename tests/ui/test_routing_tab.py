"""Smoke tests for Routing tab."""

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


def test_routing_tab_loads_after_context_refresh() -> None:
    wx = _ensure_wx_app()
    from ui.routing_tab import RoutingTab

    frame = wx.Frame(None, title="test")
    tab = RoutingTab(frame)
    frame.Show(False)

    from context.collector import collect_stretch_context

    ctx = collect_stretch_context(FIXTURES / "testproj.kicad_pro", verbose=False)
    tab.on_context_refreshed(ctx, "summary")

    assert tab._shell is not None
    assert tab._shell._btn_run is not None

    frame.Destroy()
