"""Engineering Notebook modal dialog (wxPython)."""

from __future__ import annotations

from pathlib import Path

from ui.notebook_shell import NotebookShell

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class NotebookDialog:
    """Modal Engineering Notebook dialog."""

    def __init__(self, parent: wx.Window | None, project_path: Path) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for NotebookDialog")
        self._dialog = wx.Dialog(
            parent,
            title="Engineering Notebook",
            size=(900, 760),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._shell = NotebookShell(self._dialog, project_path)
        sizer = wx.BoxSizer(wx.VERTICAL)
        close_row = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_close = wx.Button(self._dialog, label="Close")
        close_row.AddStretchSpacer()
        close_row.Add(self._btn_close)
        sizer.Add(self._shell, proportion=1, flag=wx.EXPAND)
        sizer.Add(close_row, flag=wx.EXPAND | wx.ALL, border=8)
        self._dialog.SetSizer(sizer)
        self._btn_close.Bind(wx.EVT_BUTTON, self._on_close)

    def show_modal(self) -> int:
        return self._dialog.ShowModal()

    def _on_close(self, _event: wx.CommandEvent) -> None:
        if not self._shell.confirm_discard():
            return
        self._dialog.EndModal(wx.ID_OK)


def show_notebook_dialog(
    project_path: Path | str,
    *,
    parent: wx.Window | None = None,
) -> None:
    """Show the Engineering Notebook dialog modally."""
    if wx is None:
        raise RuntimeError("wxPython is required; run inside KiCad or install wx on PYTHONPATH")
    path = Path(project_path).expanduser()
    dlg = NotebookDialog(parent, path)
    dlg.show_modal()
