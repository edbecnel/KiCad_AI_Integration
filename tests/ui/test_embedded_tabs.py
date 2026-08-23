"""Smoke tests for embedded Assistant shell tabs (ADP-011 Phase B)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ui.assistant_tab import ASSISTANT_TAB_IDS

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


@pytest.mark.parametrize("tab_id", ("chat", "datasheets", "simulation", "aerf", "notebook", "audits", "routing"))
def test_assistant_shell_embedded_tabs_load_on_refresh(tab_id: str) -> None:
    wx = _ensure_wx_app()
    from ui.assistant_shell import AssistantShell

    pro = FIXTURES / "testproj.kicad_pro"
    frame = wx.Frame(None, title="test")
    shell = AssistantShell(frame, initial_path=pro, focus_tab=tab_id)
    frame.Show(False)

    assert shell._notebook.GetSelection() == ASSISTANT_TAB_IDS.index(tab_id)
    assert shell._controller.context is not None

    idx = ASSISTANT_TAB_IDS.index(tab_id)
    page = shell._notebook.GetPage(idx)
    assert page is shell._tabs[tab_id]
    assert not page._placeholder.IsShown()
    sizer = page.GetSizer()
    assert sizer is not None
    assert not sizer.IsShown(page._placeholder)

    frame.Destroy()


def _iter_descendant_buttons(window):
    """Yield every Button under window (depth-first)."""
    import wx

    for child in window.GetChildren():
        if isinstance(child, wx.Button):
            yield child
        yield from _iter_descendant_buttons(child)


@pytest.mark.parametrize("shell_cls", ("ChatShell", "AERFShell", "SimulationShell", "DatasheetsShell"))
def test_embedded_shells_do_not_create_orphan_header_buttons(shell_cls: str) -> None:
    """Embedded shells must not create sizer-less buttons at (0,0) over the API key row."""
    wx = _ensure_wx_app()
    if shell_cls == "ChatShell":
        from ui.chat_shell import ChatShell as shell_type
    elif shell_cls == "AERFShell":
        from ui.aerf_shell import AERFShell as shell_type
    elif shell_cls == "SimulationShell":
        from ui.simulation_shell import SimulationShell as shell_type
    else:
        from ui.datasheets_shell import DatasheetsShell as shell_type

    pro = FIXTURES / "testproj.kicad_pro"
    frame = wx.Frame(None, title="test")
    panel = wx.Panel(frame)
    shell = shell_type(panel, pro, embedded=True)
    frame.Show(False)

    for button in _iter_descendant_buttons(shell):
        assert button.GetContainingSizer() is not None, (
            f"orphan button {button.GetLabel()!r} in embedded {shell_cls}"
        )

    frame.Destroy()


def test_embedded_chat_shell_uses_vertical_scroll() -> None:
    wx = _ensure_wx_app()
    from ui.chat_shell import ChatShell

    pro = FIXTURES / "testproj.kicad_pro"
    frame = wx.Frame(None, title="test")
    panel = wx.Panel(frame)
    shell = ChatShell(panel, pro, embedded=True)
    frame.Show(False)

    scroll_children = [c for c in shell.GetChildren() if isinstance(c, wx.ScrolledWindow)]
    assert len(scroll_children) == 1

    frame.Destroy()


def test_embedded_tabs_receive_updated_summary_on_refresh() -> None:
    wx = _ensure_wx_app()
    from ui.assistant_shell import AssistantShell

    pro = FIXTURES / "testproj.kicad_pro"
    frame = wx.Frame(None, title="test")
    shell = AssistantShell(frame, initial_path=pro)
    frame.Show(False)

    first_summary = shell._controller.summary_text
    assert first_summary
    shell._controller.refresh(pro)
    assert shell._summary.GetValue() == shell._controller.summary_text
    assert shell._controller.last_error is None

    frame.Destroy()
