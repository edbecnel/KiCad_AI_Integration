"""Tests for context.live.probe."""

from __future__ import annotations

import sys
import types

from context.live import probe


def test_is_pcbnew_available_with_stub() -> None:
    assert probe.is_pcbnew_available() is True


def test_get_live_board_returns_none_when_no_board() -> None:
    assert probe.get_live_board() is None


def test_get_live_board_returns_board_when_present(monkeypatch) -> None:
    class _Board:
        def IsNull(self) -> bool:
            return False

    class _Pcbnew:
        @staticmethod
        def GetBoard():
            return _Board()

    monkeypatch.setitem(sys.modules, "pcbnew", _Pcbnew)
    assert probe.get_live_board() is not None


def test_is_embedded_in_kicad_false_without_wx(monkeypatch) -> None:
    monkeypatch.setattr(probe, "load_pcbnew", lambda: object())
    import builtins

    real_import = builtins.__import__

    def _import(name, *args, **kwargs):
        if name == "wx":
            raise ImportError("no wx")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _import)
    assert probe.is_embedded_in_kicad() is False


def test_load_pcbnew_returns_module() -> None:
    mod = probe.load_pcbnew()
    assert mod is not None
    assert hasattr(mod, "GetBoard")
