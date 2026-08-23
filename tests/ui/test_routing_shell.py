"""Tests for RoutingShell approval and busy state."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

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


def test_routing_shell_run_disabled_when_routing_off() -> None:
    wx = _ensure_wx_app()
    from context.collector import collect_stretch_context
    from ui.routing_shell import RoutingShell
    from utils.config import AppConfig

    frame = wx.Frame(None, title="test")
    shell = RoutingShell(frame, FIXTURES / "testproj.kicad_pro", embedded=True)
    frame.Show(False)

    ctx = collect_stretch_context(FIXTURES / "testproj.kicad_pro", verbose=False)
    shell._cfg = AppConfig(routing_enabled=False)
    shell.apply_context(ctx)

    assert shell._btn_run.IsEnabled() is False

    frame.Destroy()


def test_routing_shell_confirm_close_blocks_when_busy() -> None:
    wx = _ensure_wx_app()
    from ui.routing_shell import RoutingShell

    frame = wx.Frame(None, title="test")
    shell = RoutingShell(frame, FIXTURES / "testproj.kicad_pro", embedded=True)
    frame.Show(False)

    shell._busy = True
    assert shell.confirm_close() is False
    shell._busy = False
    assert shell.confirm_close() is True

    frame.Destroy()


def test_routing_shell_on_run_sets_busy(monkeypatch: pytest.MonkeyPatch) -> None:
    wx = _ensure_wx_app()
    from context.collector import collect_stretch_context
    from routing.types import RoutingResult
    from ui.routing_shell import RoutingShell
    from utils.config import AppConfig

    frame = wx.Frame(None, title="test")
    shell = RoutingShell(frame, FIXTURES / "blocking_oscillator.kicad_pro", embedded=True)
    frame.Show(False)

    ctx = collect_stretch_context(
        FIXTURES / "blocking_oscillator.kicad_pro",
        verbose=False,
    )
    shell._cfg = AppConfig(routing_enabled=True)
    shell.apply_context(ctx)

    monkeypatch.setattr(
        "ui.routing_shell.wx.MessageBox",
        lambda *args, **kwargs: wx.YES,
    )

    def _fake_run(request, *, config=None):
        return RoutingResult(success=True, candidate_pcb_path=Path("/tmp/candidate.kicad_pcb"))

    quality = MagicMock()
    quality.to_dict.return_value = {"notes": []}

    monkeypatch.setattr("ui.routing_shell.run_routing", _fake_run)
    monkeypatch.setattr("ui.routing_shell.build_routing_quality_report", lambda *a, **k: quality)

    shell._on_run(MagicMock())
    assert shell._busy is True

    frame.Destroy()
