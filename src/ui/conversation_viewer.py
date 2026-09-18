"""Resizable pop-out window for reviewing Chat conversation logs."""

from __future__ import annotations

import webbrowser
from collections.abc import Callable
from pathlib import Path

from conversation.formatting import conversation_log_to_markdown
from ui.launcher import present_top_level_window
from ui.markdown_render import conversation_markdown_to_html

try:
    import wx
    import wx.html
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]
    wx.html = None  # type: ignore[assignment]


def _conversation_log_font(window: wx.Window) -> wx.Font:
    """Proportional UI font, enlarged for comfortable long-form reading."""
    base = window.GetFont()
    if not base.IsOk():
        base = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
    point_size = max(14, base.GetPointSize() + 3)
    enlarged = wx.Font(base)
    enlarged.SetPointSize(point_size)
    return enlarged


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
        self._plain_log = ""

        root = wx.BoxSizer(wx.VERTICAL)
        intro = wx.StaticText(
            self,
            label=(
                "Conversation shown as rendered markdown. "
                "Use Refresh after new replies, or leave this open while you chat."
            ),
        )
        intro.Wrap(880)
        root.Add(intro, flag=wx.EXPAND | wx.ALL, border=8)

        self._html = wx.html.HtmlWindow(self)
        self._text = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP | wx.HSCROLL,
        )
        self._text.SetFont(_conversation_log_font(self))
        self._text.Hide()
        root.Add(self._html, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)
        root.Add(self._text, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_refresh = wx.Button(self, label="Refresh")
        self._btn_copy = wx.Button(self, label="Copy")
        btn_row.Add(self._btn_refresh, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_copy, flag=wx.RIGHT, border=6)
        self._btn_save_md = wx.Button(self, label="Save as markdown…")
        btn_row.Add(self._btn_save_md, flag=wx.RIGHT, border=6)
        btn_row.AddStretchSpacer()
        self._btn_close = wx.Button(self, wx.ID_CLOSE, label="Close")
        btn_row.Add(self._btn_close)
        root.Add(btn_row, flag=wx.EXPAND | wx.ALL, border=8)

        self.SetSizer(root)
        self._btn_refresh.Bind(wx.EVT_BUTTON, self._on_refresh_clicked)
        self._btn_copy.Bind(wx.EVT_BUTTON, self._on_copy_clicked)
        self._btn_save_md.Bind(wx.EVT_BUTTON, self._on_save_markdown_clicked)
        self._btn_close.Bind(wx.EVT_BUTTON, lambda _e: self.Close())
        self._html.Bind(wx.html.EVT_HTML_LINK_CLICKED, self._on_html_link)
        self.Bind(wx.EVT_CLOSE, self._on_close)

        self._refresh_callback: Callable[[], str] | None = None
        self._markdown_callback: Callable[[], str] | None = None
        self._default_save_name = "conversation.md"

    def bind_refresh_callback(self, callback: Callable[[], str]) -> None:
        """Supply latest conversation text when the user clicks Refresh."""
        self._refresh_callback = callback

    def bind_markdown_callback(
        self,
        callback: Callable[[], str],
        *,
        default_save_name: str = "conversation.md",
    ) -> None:
        """Supply markdown export text (prefer session export over plain log)."""
        self._markdown_callback = callback
        self._default_save_name = default_save_name

    def set_content(self, text: str) -> None:
        self._plain_log = text
        self._render_markdown_view()

    def _markdown_for_view(self) -> str:
        if self._markdown_callback is not None:
            markdown = self._markdown_callback().strip()
            if markdown:
                return markdown
        converted = conversation_log_to_markdown(self._plain_log).strip()
        if converted:
            return converted
        plain = self._plain_log.strip()
        if plain and not plain.startswith("(No messages yet"):
            return conversation_log_to_markdown(plain) or plain
        return ""

    def _render_markdown_view(self) -> None:
        markdown = self._markdown_for_view()
        if not markdown:
            markdown = "_No messages yet — send a question to start the conversation._"
        html_document = conversation_markdown_to_html(markdown)
        self._html.Show()
        self._text.Hide()
        if not self._html.SetPage(html_document):
            self._html.Hide()
            self._text.Show()
            self._text.SetValue(self._plain_log)
            self._text.ShowPosition(0)
        self.Layout()

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
        text = self._markdown_for_view() or self._plain_log
        if not text.strip():
            wx.MessageBox("Conversation is empty.", "Copy", wx.OK | wx.ICON_INFORMATION)
            return
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()

    def _on_html_link(self, event: wx.html.HtmlLinkClickedEvent) -> None:
        href = event.GetLinkInfo().GetHref()
        if href.lower().startswith(("http://", "https://", "file://")):
            webbrowser.open(href)

    def _on_save_markdown_clicked(self, _event: wx.CommandEvent) -> None:
        markdown = self._markdown_for_view()
        if not markdown:
            wx.MessageBox(
                "Conversation is empty.",
                "Save as markdown",
                wx.OK | wx.ICON_INFORMATION,
            )
            return
        default_dir = str(Path.home())
        with wx.FileDialog(
            self,
            "Save conversation as Markdown",
            defaultDir=default_dir,
            defaultFile=self._default_save_name,
            wildcard="Markdown files (*.md)|*.md",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            path = Path(dlg.GetPath())
            if path.suffix.lower() != ".md":
                path = path.with_suffix(".md")
            try:
                path.write_text(markdown + "\n", encoding="utf-8")
            except OSError as exc:
                wx.MessageBox(
                    f"Could not save file:\n{exc}",
                    "Save as markdown",
                    wx.OK | wx.ICON_ERROR,
                )

    def _on_close(self, event: wx.CloseEvent) -> None:
        if self._on_closed is not None:
            self._on_closed()
        event.Skip()


def show_conversation_viewer(
    parent: wx.Window | None,
    text: str,
    *,
    refresh_callback: Callable[[], str] | None = None,
    markdown_callback: Callable[[], str] | None = None,
    default_save_name: str = "conversation.md",
    on_closed: Callable[[], None] | None = None,
) -> ConversationViewerFrame:
    """Show a resizable conversation viewer (non-modal)."""
    if wx is None:
        raise RuntimeError("wxPython is required for show_conversation_viewer")
    frame = ConversationViewerFrame(parent, on_closed=on_closed)
    if refresh_callback is not None:
        frame.bind_refresh_callback(refresh_callback)
    if markdown_callback is not None:
        frame.bind_markdown_callback(
            markdown_callback,
            default_save_name=default_save_name,
        )
    frame.set_content(text)
    present_top_level_window(frame, parent)
    return frame
