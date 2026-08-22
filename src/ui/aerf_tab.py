"""Embedded AERF tab for the Assistant shell."""

from __future__ import annotations

from pathlib import Path

from context.model import ProjectContext
from ui.aerf_shell import AERFShell
from ui.assistant_tab import AssistantTabPanel

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class AERFTab(AssistantTabPanel):
    """Hosts AERFShell inline."""

    def __init__(self, parent: wx.Window) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for AERFTab")
        super().__init__(parent)
        self._loaded_path: Path | None = None
        self._shell: AERFShell | None = None

        self._placeholder = wx.StaticText(
            self,
            label="Select a project and click Refresh context to run AERF stages.",
        )
        self._placeholder.Wrap(700)

        self._shell_slot = wx.Panel(self)
        self._shell_sizer = wx.BoxSizer(wx.VERTICAL)
        self._shell_slot.SetSizer(self._shell_sizer)

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(self._placeholder, flag=wx.ALL, border=10)
        root.Add(self._shell_slot, proportion=1, flag=wx.EXPAND)
        self.SetSizer(root)

    def on_context_refreshed(self, ctx: ProjectContext, summary: str) -> None:
        new_path = Path(ctx.project_path).expanduser().resolve()
        if self._shell is not None and self._loaded_path == new_path:
            self._shell.apply_context(ctx)
            return
        if self._shell is not None:
            self._clear_shell()

        self._loaded_path = new_path
        self._hide_placeholder()
        self._shell = AERFShell(self._shell_slot, new_path, embedded=True)
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
