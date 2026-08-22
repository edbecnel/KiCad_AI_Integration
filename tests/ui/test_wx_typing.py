"""Regression tests for KiCad embedded Python 3.9 + wx typing compatibility."""

from __future__ import annotations

import sys
import types


def test_modal_opener_import_without_pep604_wx_union() -> None:
    """ModalOpener must not use wx.Window | None at runtime (KiCad 3.9 TypeError)."""
    from ui.wx_typing import ModalOpener

    assert ModalOpener is not None


def test_placeholder_tab_imports_modal_opener_alias() -> None:
    from ui.placeholder_tab import PlaceholderTab
    from ui.wx_typing import ModalOpener

    assert PlaceholderTab is not None
    assert ModalOpener is not None


def test_assistant_shell_import_with_sip_like_wx_window() -> None:
    """Simulate wx SIP types that reject PEP 604 ``|`` at runtime."""
    wx_mod = types.ModuleType("wx")

    class _SipLike:
        """Mimics wx SIP wrapper: ``type | None`` raises TypeError."""

        def __or__(self, other: object) -> object:
            raise TypeError(f"unsupported operand type(s) for |: {type(self)!r} and {type(other)!r}")

    class Window(_SipLike):
        pass

    class Panel(Window):
        pass

    class Frame(Window):
        pass

    class BoxSizer:
        def __init__(self, _orient: int) -> None:
            self._items: list = []

        def Add(self, *args, **kwargs) -> None:
            pass

        def Clear(self, *_args) -> None:
            pass

    class StaticText:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def Wrap(self, _width: int) -> None:
            pass

        def Hide(self) -> None:
            pass

        def Show(self) -> None:
            pass

    class TextCtrl:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def SetValue(self, _value: str) -> None:
            pass

        def SetMinSize(self, _size) -> None:
            pass

    class Button:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def Bind(self, *_args, **_kwargs) -> None:
            pass

        def Enable(self, _enabled: bool) -> None:
            pass

    class Notebook:
        def __init__(self, _parent) -> None:
            self._pages: list = []
            self._selection = 0

        def AddPage(self, page, _label: str) -> None:
            self._pages.append(page)

        def GetSelection(self) -> int:
            return self._selection

        def SetSelection(self, idx: int) -> None:
            self._selection = idx

        def GetPage(self, idx: int):
            return self._pages[idx]

        def Bind(self, *_args, **_kwargs) -> None:
            pass

    class FileDialog:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def ShowModal(self) -> int:
            return 0

        def GetPath(self) -> str:
            return ""

        def Destroy(self) -> None:
            pass

    class App:
        def __init__(self, _redirect: bool) -> None:
            pass

        def IsMainLoopRunning(self) -> bool:
            return False

        def MainLoop(self) -> None:
            pass

    wx_mod.Window = Window
    wx_mod.Panel = Panel
    wx_mod.Frame = Frame
    wx_mod.BoxSizer = BoxSizer
    wx_mod.StaticText = StaticText
    wx_mod.TextCtrl = TextCtrl
    wx_mod.Button = Button
    wx_mod.Notebook = Notebook
    wx_mod.FileDialog = FileDialog
    wx_mod.App = App
    wx_mod.VERTICAL = wx_mod.HORIZONTAL = wx_mod.EXPAND = wx_mod.ALL = 0
    wx_mod.RIGHT = wx_mod.LEFT = wx_mod.TOP = wx_mod.BOTTOM = 0
    wx_mod.ALIGN_CENTER_VERTICAL = 0
    wx_mod.TE_MULTILINE = wx_mod.TE_READONLY = 0
    wx_mod.DEFAULT_FRAME_STYLE = wx_mod.FD_OPEN = wx_mod.FD_FILE_MUST_EXIST = 0
    wx_mod.ID_OK = 0
    wx_mod.EVT_BUTTON = wx_mod.EVT_NOTEBOOK_PAGE_CHANGED = object()
    wx_mod.EVT_CLOSE = object()
    wx_mod.GetApp = lambda: None

  # PEP 604 with SIP-like type must fail (documents why we use Optional)
    with_sip = _SipLike()
    try:
        with_sip | None  # type: ignore[operator]
        assert False, "expected TypeError from SIP-like | None"
    except TypeError:
        pass

    saved = sys.modules.get("wx")
    sys.modules["wx"] = wx_mod
    for name in list(sys.modules):
        if name.startswith("ui."):
            del sys.modules[name]
    try:
        import ui.wx_typing  # noqa: F401
        import ui.placeholder_tab  # noqa: F401
        import ui.assistant_tab  # noqa: F401
    finally:
        if saved is None:
            sys.modules.pop("wx", None)
        else:
            sys.modules["wx"] = saved
        for name in list(sys.modules):
            if name.startswith("ui."):
                del sys.modules[name]
