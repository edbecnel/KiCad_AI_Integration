"""Embedded Routing tab for the Assistant shell."""

from __future__ import annotations

from pathlib import Path

from context.model import ProjectContext
from ui.assistant_tab import AssistantTabPanel
from ui.routing_shell import RoutingShell

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class RoutingTab(AssistantTabPanel):
    """Hosts RoutingShell inline."""

    HELP_TOPIC_ID = "routing"

    def __init__(self, parent: wx.Window) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for RoutingTab")
        super().__init__(parent)
        self._loaded_path: Path | None = None
        self._shell: RoutingShell | None = None

        self._placeholder = wx.StaticText(
            self,
            label="Select a project and click Refresh context to use autorouting.",
        )
        self._placeholder.Wrap(700)

        self._shell_slot = wx.Panel(self)
        self._shell_sizer = wx.BoxSizer(wx.VERTICAL)
        self._shell_slot.SetSizer(self._shell_sizer)

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(self.build_help_row(), flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=4)
        root.Add(self._placeholder, flag=wx.ALL, border=10)
        root.Add(self._shell_slot, proportion=1, flag=wx.EXPAND)
        self.SetSizer(root)

    def confirm_discard(self) -> bool:
        if self._shell is None:
            return True
        return self._shell.confirm_close()

    def on_context_refreshed(self, ctx: ProjectContext, summary: str) -> None:
        new_path = Path(ctx.project_path).expanduser().resolve()
        if self._shell is not None and self._loaded_path == new_path:
            self._shell.apply_context(ctx)
            return
        if self._shell is not None:
            if not self._shell.confirm_close():
                return
            self._clear_shell()

        self._loaded_path = new_path
        self._hide_placeholder()
        self._shell = RoutingShell(self._shell_slot, new_path, embedded=True)
        self._shell_sizer.Add(self._shell, proportion=1, flag=wx.EXPAND)
        self._shell.apply_context(ctx)
        self._shell_slot.Layout()
        self.Layout()

    def _clear_shell(self) -> None:
        if self._shell is not None:
            self._shell.Destroy()
            self._shell = None
        self._shell_sizer.Clear(False)
        self._loaded_path = None
        self._show_placeholder()
