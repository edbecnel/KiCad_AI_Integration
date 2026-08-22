"""Tests for KiCad editor parent window resolution (macOS full-screen UX)."""

from __future__ import annotations

import sys
import types


def test_resolve_kicad_parent_window_returns_none_without_wx_app() -> None:
    from ui.launcher import resolve_kicad_parent_window

    assert resolve_kicad_parent_window() is None


def test_resolve_ui_parent_prefers_explicit_parent() -> None:
    from ui.launcher import resolve_ui_parent

    sentinel = object()
    assert resolve_ui_parent(sentinel) is sentinel


def test_resolve_kicad_parent_window_finds_pcb_frame() -> None:
    wx_mod = types.ModuleType("wx")

    class Frame:
        def __init__(self, name: str = "") -> None:
            self._name = name

        def GetName(self) -> str:
            return self._name

    class App:
        def __init__(self) -> None:
            self._top = Frame("KiPython")

        def IsMainLoopRunning(self) -> bool:
            return True

        def GetTopWindow(self):
            return self._top

    pcb_frame = Frame("PcbFrame")

    def find_window_by_name(name: str):
        if name == "PcbFrame":
            return pcb_frame
        return None

    wx_mod.App = App
    wx_mod.FindWindowByName = find_window_by_name
    wx_mod.Window = Frame
    wx_mod.GetApp = lambda: App()

    saved = sys.modules.get("wx")
    sys.modules["wx"] = wx_mod
    try:
        from ui.launcher import resolve_kicad_parent_window

        assert resolve_kicad_parent_window() is pcb_frame
    finally:
        if saved is None:
            sys.modules.pop("wx", None)
        else:
            sys.modules["wx"] = saved


def test_resolve_kicad_parent_window_skips_kipython_top_window() -> None:
    wx_mod = types.ModuleType("wx")

    class Frame:
        def __init__(self, name: str = "") -> None:
            self._name = name

        def GetName(self) -> str:
            return self._name

    class App:
        def IsMainLoopRunning(self) -> bool:
            return True

        def GetTopWindow(self):
            return Frame("KiPython")

    wx_mod.App = App
    wx_mod.FindWindowByName = lambda _name: None
    wx_mod.Window = Frame
    wx_mod.GetApp = lambda: App()

    saved = sys.modules.get("wx")
    sys.modules["wx"] = wx_mod
    try:
        from ui.launcher import resolve_kicad_parent_window

        assert resolve_kicad_parent_window() is None
    finally:
        if saved is None:
            sys.modules.pop("wx", None)
        else:
            sys.modules["wx"] = saved
