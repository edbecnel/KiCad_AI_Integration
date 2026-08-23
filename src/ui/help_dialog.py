"""In-app User Guide viewer with rendered markdown."""

from __future__ import annotations

import html
import re
import webbrowser

from ui.launcher import present_top_level_window
from ui.markdown_render import markdown_to_html, write_temp_html
from ui.user_guide_supply import (
    load_manifest,
    read_guide_markdown,
    resolve_guide_href,
    user_guides_dir,
)

try:
    import wx
    import wx.html
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]
    wx.html = None  # type: ignore[assignment]

_user_guide_frame: object | None = None


class UserGuideFrame(wx.Frame if wx else object):  # type: ignore[misc]
    """Non-modal Help / User Guide browser."""

    def __init__(self, parent: wx.Window | None = None) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for UserGuideFrame")
        super().__init__(
            parent,
            title="KiCad AI — User Guide",
            size=(980, 720),
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER,
        )
        self._guides_dir = user_guides_dir()
        self._manifest = load_manifest(self._guides_dir)
        self._current_rel_path = self._manifest.default_topic
        self._topic_by_path = {topic.rel_path: topic for topic in self._manifest.topics}

        root = wx.BoxSizer(wx.VERTICAL)

        toolbar = wx.BoxSizer(wx.HORIZONTAL)
        toolbar.Add(
            wx.StaticText(self, label="Browse the KiCad AI User Guide."),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            border=8,
        )
        toolbar.AddStretchSpacer()
        self._btn_browser = wx.Button(self, label="Open in browser")
        self._btn_close = wx.Button(self, wx.ID_CLOSE, label="Close")
        toolbar.Add(self._btn_browser, flag=wx.RIGHT, border=6)
        toolbar.Add(self._btn_close)
        root.Add(toolbar, flag=wx.EXPAND | wx.ALL, border=8)

        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE | wx.SP_3D)
        self._tree_panel = wx.Panel(splitter)
        tree_sizer = wx.BoxSizer(wx.VERTICAL)
        tree_sizer.Add(wx.StaticText(self._tree_panel, label="Contents"), flag=wx.ALL, border=6)
        self._tree = wx.TreeCtrl(self._tree_panel, style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT)
        tree_sizer.Add(self._tree, proportion=1, flag=wx.EXPAND | wx.ALL, border=6)
        self._tree_panel.SetSizer(tree_sizer)

        self._content_panel = wx.Panel(splitter)
        content_sizer = wx.BoxSizer(wx.VERTICAL)
        self._title = wx.StaticText(self._content_panel, label="")
        font = self._title.GetFont()
        font.SetPointSize(font.GetPointSize() + 2)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self._title.SetFont(font)
        content_sizer.Add(self._title, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=8)

        self._html = wx.html.HtmlWindow(self._content_panel)
        content_sizer.Add(self._html, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)
        self._fallback = wx.TextCtrl(
            self._content_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
        )
        self._fallback.Hide()
        content_sizer.Add(self._fallback, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)
        self._content_panel.SetSizer(content_sizer)

        splitter.SplitVertically(self._tree_panel, self._content_panel, sashPosition=260)
        splitter.SetMinimumPaneSize(180)
        root.Add(splitter, proportion=1, flag=wx.EXPAND | wx.ALL, border=4)

        self._status = wx.StaticText(self, label="")
        root.Add(self._status, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)
        self.SetSizer(root)

        self._populate_tree()
        self._btn_browser.Bind(wx.EVT_BUTTON, self._on_open_in_browser)
        self._btn_close.Bind(wx.EVT_BUTTON, lambda _e: self.Close())
        self._tree.Bind(wx.EVT_TREE_SEL_CHANGED, self._on_tree_selection)
        self._html.Bind(wx.html.EVT_HTML_LINK_CLICKED, self._on_html_link)

        self.load_topic(self._manifest.default_topic)

    def load_topic(self, topic: str | None) -> None:
        rel_path = self._manifest.path_for_topic(topic)
        self._show_guide(rel_path)

    def load_tab_help(self, tab_id: str) -> None:
        rel_path = self._manifest.path_for_tab(tab_id)
        self._show_guide(rel_path)

    def _show_guide(self, rel_path: str) -> None:
        self._current_rel_path = rel_path
        try:
            markdown_text = read_guide_markdown(rel_path, self._guides_dir)
        except (OSError, ValueError) as exc:
            self._title.SetLabel("User Guide")
            self._set_html_content(
                markdown_to_html(
                    f"# Guide not found\n\nCould not load `{rel_path}`:\n\n{exc}",
                    title="User Guide",
                )
            )
            self._status.SetLabel(str(exc))
            return

        topic = self._topic_by_path.get(rel_path)
        title = topic.title if topic else rel_path
        self._title.SetLabel(title)
        self._set_html_content(markdown_to_html(markdown_text, title=title))
        self._status.SetLabel(str(self._guides_dir / rel_path))
        self._select_tree_for_path(rel_path)

    def _set_html_content(self, html_document: str) -> None:
        self._fallback.Hide()
        self._html.Show()
        if not self._html.SetPage(html_document):
            self._html.Hide()
            self._fallback.Show()
            self._fallback.SetValue(_html_to_plain_text(html_document))
        self._content_panel.Layout()

    def _populate_tree(self) -> None:
        self._tree.DeleteAllItems()
        root = self._tree.AddRoot("User Guides")
        by_id = self._manifest.topic_by_id
        for section in self._manifest.sections:
            section_item = self._tree.AppendItem(root, section.title)
            self._tree.SetItemData(section_item, "")
            for topic_id in section.topic_ids:
                topic = by_id[topic_id]
                item = self._tree.AppendItem(section_item, topic.title)
                self._tree.SetItemData(item, topic.rel_path)
            self._tree.Expand(section_item)

    def _select_tree_for_path(self, rel_path: str) -> None:
        root = self._tree.GetRootItem()
        self._select_tree_item_for_path(root, rel_path)

    def _select_tree_item_for_path(self, parent: wx.TreeItemId, rel_path: str) -> bool:
        child, cookie = self._tree.GetFirstChild(parent)
        while child.IsOk():
            data = self._tree.GetItemData(child)
            if data == rel_path:
                self._tree.SelectItem(child)
                return True
            if self._select_tree_item_for_path(child, rel_path):
                return True
            child, cookie = self._tree.GetNextChild(parent, cookie)
        return False

    def _on_tree_selection(self, event: wx.TreeEvent) -> None:
        rel_path = self._tree.GetItemData(event.GetItem())
        if isinstance(rel_path, str) and rel_path and rel_path != self._current_rel_path:
            self._show_guide(rel_path)
        event.Skip()

    def _on_html_link(self, event: wx.html.HtmlLinkClickedEvent) -> None:
        href = event.GetLinkInfo().GetHref()
        resolved = resolve_guide_href(href, self._current_rel_path, self._guides_dir)
        if resolved is not None:
            self._show_guide(resolved)
            return
        if href.lower().startswith(("http://", "https://")):
            webbrowser.open(href)
            return
        event.Skip()

    def _on_open_in_browser(self, _event: wx.CommandEvent) -> None:
        try:
            markdown_text = read_guide_markdown(self._current_rel_path, self._guides_dir)
        except OSError as exc:
            wx.MessageBox(str(exc), "User Guide", wx.OK | wx.ICON_ERROR)
            return
        topic = self._topic_by_path.get(self._current_rel_path)
        title = topic.title if topic else self._current_rel_path
        temp_path = write_temp_html(markdown_to_html(markdown_text, title=title))
        webbrowser.open(temp_path.as_uri())


def show_user_guide(
    parent: wx.Window | None = None,
    *,
    topic: str | None = None,
    tab_id: str | None = None,
) -> object | None:
    """Show or raise the singleton User Guide frame."""
    if wx is None:
        raise RuntimeError("wxPython is required for show_user_guide")

    global _user_guide_frame
    frame = _user_guide_frame
    if frame is not None:
        try:
            if isinstance(frame, UserGuideFrame):
                if not frame.IsShown():
                    present_top_level_window(frame, parent)
                else:
                    frame.Raise()
                if tab_id:
                    frame.load_tab_help(tab_id)
                elif topic:
                    frame.load_topic(topic)
                return frame
        except RuntimeError:
            _user_guide_frame = None

    if frame is not None:
        try:
            frame.Destroy()
        except RuntimeError:
            pass
        _user_guide_frame = None

    frame = UserGuideFrame(parent)
    frame.Bind(wx.EVT_CLOSE, _on_frame_closed)
    present_top_level_window(frame, parent)
    _user_guide_frame = frame
    if tab_id:
        frame.load_tab_help(tab_id)
    elif topic:
        frame.load_topic(topic)
    return frame


def _on_frame_closed(event: wx.CloseEvent) -> None:
    global _user_guide_frame
    _user_guide_frame = None
    event.Skip()


def reset_user_guide_for_tests() -> None:
    """Clear singleton state (tests only)."""
    global _user_guide_frame
    _user_guide_frame = None


def _html_to_plain_text(html_document: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html_document, flags=re.I | re.S)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p>", "\n\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()
