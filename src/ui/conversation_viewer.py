"""Resizable pop-out window for reviewing Chat conversation logs."""

from __future__ import annotations

from collections.abc import Callable

from ui.launcher import present_top_level_window

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class ConversationViewerFrame(wx.Frame if wx else object):  # type: ignore[misc]
    """Non-modal, resizable viewer for the Chat conversation log."""

    def __init__(
        self,
        parent: wx.Window | None,
        *,
        on_closed: Callable[[], None] | None = None,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for ConversationViewerFrame")
        super().__init__(
            parent,
            title="KiCad AI — Conversation",
            size=(920, 640),
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER,
        )
        self._on_closed = on_closed

        root = wx.BoxSizer(wx.VERTICAL)
        intro = wx.StaticText(
            self,
            label="Full conversation log. Use Refresh after new replies, or leave this open while you chat.",
        )
        intro.Wrap(880)
        root.Add(intro, flag=wx.EXPAND | wx.ALL, border=8)

        self._text = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP | wx.HSCROLL,
        )
        font = wx.Font(wx.FontInfo(11).Family(wx.FONTFAMILY_TELETYPE))
        if font.IsOk():
            self._text.SetFont(font)
        root.Add(self._text, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_refresh = wx.Button(self, label="Refresh")
        self._btn_copy = wx.Button(self, label="Copy")
        btn_row.Add(self._btn_refresh, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_copy, flag=wx.RIGHT, border=6)
        btn_row.AddStretchSpacer()
        self._btn_close = wx.Button(self, wx.ID_CLOSE, label="Close")
        btn_row.Add(self._btn_close)
        root.Add(btn_row, flag=wx.EXPAND | wx.ALL, border=8)

        self.SetSizer(root)
        self._btn_refresh.Bind(wx.EVT_BUTTON, self._on_refresh_clicked)
        self._btn_copy.Bind(wx.EVT_BUTTON, self._on_copy_clicked)
        self._btn_close.Bind(wx.EVT_BUTTON, lambda _e: self.Close())
        self.Bind(wx.EVT_CLOSE, self._on_close)

        self._refresh_callback: Callable[[], str] | None = None

    def bind_refresh_callback(self, callback: Callable[[], str]) -> None:
        """Supply latest conversation text when the user clicks Refresh."""
        self._refresh_callback = callback

    def set_content(self, text: str) -> None:
        self._text.SetValue(text)
        self._text.ShowPosition(0)

    def _on_refresh_clicked(self, _event: wx.CommandEvent) -> None:
        if self._refresh_callback is not None:
            self.set_content(self._refresh_callback())
        else:
            wx.MessageBox(
                "Nothing to refresh.",
                "Conversation",
                wx.OK | wx.ICON_INFORMATION,
            )

    def _on_copy_clicked(self, _event: wx.CommandEvent) -> None:
        text = self._text.GetValue()
        if not text.strip():
            wx.MessageBox("Conversation is empty.", "Copy", wx.OK | wx.ICON_INFORMATION)
            return
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()

    def _on_close(self, event: wx.CloseEvent) -> None:
        if self._on_closed is not None:
            self._on_closed()
        event.Skip()


def show_conversation_viewer(
    parent: wx.Window | None,
    text: str,
    *,
    refresh_callback: Callable[[], str] | None = None,
    on_closed: Callable[[], None] | None = None,
) -> ConversationViewerFrame:
    """Show a resizable conversation viewer (non-modal)."""
    if wx is None:
        raise RuntimeError("wxPython is required for show_conversation_viewer")
    frame = ConversationViewerFrame(parent, on_closed=on_closed)
    if refresh_callback is not None:
        frame.bind_refresh_callback(refresh_callback)
    frame.set_content(text)
    present_top_level_window(frame, parent)
    return frame
