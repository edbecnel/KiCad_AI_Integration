"""KiCad dockable panel adapter for the Assistant shell (Phase 2 stub)."""

from __future__ import annotations

from pathlib import Path

from ui.assistant_shell import AssistantShell

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class AssistantDockPanel(wx.Panel):
    """Thin embedding wrapper; KiCad ActionPlugin registration deferred to Sprint 4."""

    def __init__(
        self,
        parent: wx.Window,
        initial_path: Path | str | None = None,
        *,
        focus_tab: str | None = None,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for AssistantDockPanel")
        super().__init__(parent)
        self._shell = AssistantShell(self, initial_path=initial_path, focus_tab=focus_tab)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._shell, proportion=1, flag=wx.EXPAND)
        self.SetSizer(sizer)

    def confirm_close(self) -> bool:
        return self._shell.confirm_close()

    def open_placeholder_panel(self, tab_id: str) -> None:
        self._shell.open_placeholder_panel(tab_id)
