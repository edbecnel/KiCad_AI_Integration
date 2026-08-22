"""Modal wrapper for the embeddable chat panel."""

from __future__ import annotations

from pathlib import Path

from ui.chat_shell import ChatShell

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class ChatDialog:
    """Modal dialog hosting ChatShell."""

    def __init__(
        self,
        parent: wx.Window | None,
        project_path: Path,
        *,
        retry_failed_urls: bool = False,
        force_refresh_urls: bool = False,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for ChatDialog")
        self._dialog = wx.Dialog(
            parent,
            title="KiCad AI Assistant",
            size=(780, 640),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._shell = ChatShell(
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


def show_chat_dialog(
    project_path: Path | str,
    *,
    parent: wx.Window | None = None,
    retry_failed_urls: bool = False,
    force_refresh_urls: bool = False,
) -> None:
    """Show the KiCad AI chat dialog modally."""
    if wx is None:
        raise RuntimeError("wxPython is required; run inside KiCad or install wx on PYTHONPATH")
    path = Path(project_path).expanduser()
    dlg = ChatDialog(
        parent,
        path,
        retry_failed_urls=retry_failed_urls,
        force_refresh_urls=force_refresh_urls,
    )
    dlg.show_modal()
