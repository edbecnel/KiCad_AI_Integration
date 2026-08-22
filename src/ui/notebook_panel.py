"""Engineering Notebook non-modal panel for KiCad embedding (ADP-003 §13)."""

from __future__ import annotations

from pathlib import Path

from ui.notebook_shell import NotebookShell

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class NotebookPanelFrame(wx.Frame):
    """Top-level frame hosting the notebook panel (dev / Scripting Console)."""

    def __init__(self, project_path: Path, parent: wx.Window | None = None) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for NotebookPanelFrame")
        super().__init__(
            parent,
            title="Engineering Notebook",
            size=(900, 760),
            style=wx.DEFAULT_FRAME_STYLE,
        )
        self._shell = NotebookShell(self, project_path)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._shell, proportion=1, flag=wx.EXPAND)
        self.SetSizer(sizer)
        self.Bind(wx.EVT_CLOSE, self._on_close)

    def _on_close(self, event: wx.CloseEvent) -> None:
        if not self._shell.confirm_discard():
            event.Veto()
            return
        event.Skip()


def show_notebook_panel(
    project_path: Path | str,
    *,
    parent: wx.Window | None = None,
) -> NotebookPanelFrame | None:
    """Show a non-modal Engineering Notebook frame."""
    if wx is None:
        raise RuntimeError("wxPython is required; run inside KiCad or install wx on PYTHONPATH")
    from ui.launcher import present_top_level_window, run_wx_main_loop_if_needed
    from ui.kicad_host import prepare_kicad_ui_launch

    ok, kicad_parent = prepare_kicad_ui_launch(parent)
    if not ok:
        return None
    path = Path(project_path).expanduser()
    frame = NotebookPanelFrame(path, parent=kicad_parent)
    present_top_level_window(frame, kicad_parent)
    run_wx_main_loop_if_needed()
    return frame
