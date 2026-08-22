"""Modal wrapper for the embeddable datasheets panel."""

from __future__ import annotations

from pathlib import Path

from ui.datasheets_shell import DatasheetsShell

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class MissingDatasheetsDialog:
    """Modal dialog hosting DatasheetsShell."""

    def __init__(
        self,
        parent: wx.Window | None,
        project_path: Path,
        *,
        retry_failed_urls: bool = False,
        force_refresh_urls: bool = False,
        ai_datasheets: bool = False,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for MissingDatasheetsDialog")
        self._dialog = wx.Dialog(
            parent,
            title="Datasheets",
            size=(840, 680),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._shell = DatasheetsShell(
            self._dialog,
            project_path,
            embedded=False,
            retry_failed_urls=retry_failed_urls,
            force_refresh_urls=force_refresh_urls,
            ai_datasheets=ai_datasheets,
        )
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._shell, proportion=1, flag=wx.EXPAND)
        self._dialog.SetSizer(sizer)
        self._dialog.SetMinSize((840, 640))
        self._dialog.Bind(wx.EVT_CLOSE, self._on_close)
        self._dialog.CentreOnParent()

    def show_modal(self) -> int:
        return self._dialog.ShowModal()

    def _on_close(self, event: wx.CloseEvent) -> None:
        if not self._shell.confirm_close():
            event.Veto()
            return
        event.Skip()


def show_missing_datasheets_dialog(
    project_path: Path | str,
    *,
    parent: wx.Window | None = None,
    retry_failed_urls: bool = False,
    force_refresh_urls: bool = False,
    ai_datasheets: bool = False,
) -> None:
    """Show the datasheets dialog modally."""
    if wx is None:
        raise RuntimeError("wxPython is required; run inside KiCad or install wx on PYTHONPATH")
    path = Path(project_path).expanduser()
    dlg = MissingDatasheetsDialog(
        parent,
        path,
        retry_failed_urls=retry_failed_urls,
        force_refresh_urls=force_refresh_urls,
        ai_datasheets=ai_datasheets,
    )
    dlg.show_modal()
