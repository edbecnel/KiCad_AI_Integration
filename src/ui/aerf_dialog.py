"""Modal wrapper for the embeddable AERF panel."""

from __future__ import annotations

from pathlib import Path

from ui.aerf_shell import AERFShell

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class AERFDialog:
    """Modal dialog hosting AERFShell."""

    def __init__(
        self,
        parent: wx.Window | None,
        project_path: Path,
        *,
        retry_failed_urls: bool = False,
        force_refresh_urls: bool = False,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for AERFDialog")
        self._dialog = wx.Dialog(
            parent,
            title="AERF Staged Analysis",
            size=(820, 700),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._shell = AERFShell(
            self._dialog,
            project_path,
            embedded=False,
            retry_failed_urls=retry_failed_urls,
            force_refresh_urls=force_refresh_urls,
        )
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._shell, proportion=1, flag=wx.EXPAND)
        self._dialog.SetSizer(sizer)

    def show_modal(self) -> int:
        return self._dialog.ShowModal()


def show_aerf_dialog(
    project_path: Path | str,
    *,
    parent: wx.Window | None = None,
    retry_failed_urls: bool = False,
    force_refresh_urls: bool = False,
) -> None:
    """Show the AERF staged analysis dialog modally."""
    if wx is None:
        raise RuntimeError("wxPython is required; run inside KiCad or install wx on PYTHONPATH")
    path = Path(project_path).expanduser()
    dlg = AERFDialog(
        parent,
        path,
        retry_failed_urls=retry_failed_urls,
        force_refresh_urls=force_refresh_urls,
    )
    dlg.show_modal()
