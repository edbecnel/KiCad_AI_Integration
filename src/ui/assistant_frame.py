"""Standalone wx.Frame host for the Assistant shell (Terminal --ui)."""

from __future__ import annotations

from pathlib import Path

from ui.assistant_shell import AssistantShell

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class AssistantFrame(wx.Frame):
    """Top-level frame hosting AssistantShell."""

    def __init__(
        self,
        parent: wx.Window | None,
        initial_path: Path | str | None = None,
        *,
        focus_tab: str | None = None,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for AssistantFrame")
        super().__init__(
            parent,
            title="KiCad AI Assistant",
            size=(900, 760),
            style=wx.DEFAULT_FRAME_STYLE,
        )
        self._shell = AssistantShell(self, initial_path=initial_path, focus_tab=focus_tab)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._shell, proportion=1, flag=wx.EXPAND)
        self.SetSizer(sizer)
        self.Bind(wx.EVT_CLOSE, self._on_close)

    def open_placeholder_panel(self, tab_id: str) -> None:
        self._shell.open_placeholder_panel(tab_id)

    def _on_close(self, event: wx.CloseEvent) -> None:
        if not self._shell.confirm_close():
            event.Veto()
            return
        event.Skip()
