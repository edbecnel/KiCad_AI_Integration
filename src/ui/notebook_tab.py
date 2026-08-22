"""Embedded Engineering Notebook tab for the Assistant shell."""

from __future__ import annotations

from pathlib import Path

from context.model import ProjectContext
from ui.assistant_tab import AssistantTabPanel
from ui.notebook_shell import NotebookShell

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class NotebookTab(AssistantTabPanel):
    """Hosts NotebookShell inline; recreates when project path changes."""

    def __init__(self, parent: wx.Window) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for NotebookTab")
        super().__init__(parent)
        self._loaded_path: Path | None = None
        self._shell: NotebookShell | None = None

        self._placeholder = wx.StaticText(
            self,
            label="Select a project and click Refresh context to load the Engineering Notebook.",
        )
        self._placeholder.Wrap(700)

        self._shell_slot = wx.Panel(self)
        self._shell_sizer = wx.BoxSizer(wx.VERTICAL)
        self._shell_slot.SetSizer(self._shell_sizer)

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(self._placeholder, flag=wx.ALL, border=10)
        root.Add(self._shell_slot, proportion=1, flag=wx.EXPAND)
        self.SetSizer(root)

    def confirm_discard(self) -> bool:
        if self._shell is None:
            return True
        return self._shell.confirm_discard()

    def on_context_refreshed(self, ctx: ProjectContext, summary: str) -> None:
        new_path = Path(ctx.project_path).expanduser().resolve()
        if self._shell is not None and self._loaded_path == new_path:
            return
        if self._shell is not None:
            if not self._shell.confirm_discard():
                return
            self._clear_shell()

        self._loaded_path = new_path
        self._placeholder.Hide()
        self._shell = NotebookShell(self._shell_slot, new_path)
        self._shell_sizer.Add(self._shell, proportion=1, flag=wx.EXPAND)
        self._shell_slot.Layout()
        self.Layout()

    def _clear_shell(self) -> None:
        if self._shell is not None:
            self._shell.Destroy()
            self._shell = None
        self._shell_sizer.Clear(False)
        self._loaded_path = None
        self._placeholder.Show()
