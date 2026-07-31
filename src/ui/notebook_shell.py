"""Shared Engineering Notebook shell (search, renderer, save/reload)."""

from __future__ import annotations

import json
from pathlib import Path
from ekm.errors import EKMError
from ui.notebook_renderer import build_sections_container
from ui.notebook_supply import EKMViewModel, create_view_model

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class NotebookShell(wx.Panel):
    """Reusable notebook body: search, section renderer, optional JSON tab."""

    def __init__(self, parent: wx.Window, project_path: Path) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for NotebookShell")
        super().__init__(parent)
        self._project_path = project_path.expanduser().resolve()
        self._vm = create_view_model(self._project_path)
        self._section_widgets: list = []

        root = wx.BoxSizer(wx.VERTICAL)
        self._summary = wx.StaticText(self, label="")
        root.Add(self._summary, flag=wx.ALL, border=8)

        search_row = wx.BoxSizer(wx.HORIZONTAL)
        search_row.Add(wx.StaticText(self, label="Search:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=6)
        self._search = wx.TextCtrl(self)
        self._btn_clear_search = wx.Button(self, label="Clear")
        search_row.Add(self._search, proportion=1, flag=wx.RIGHT, border=6)
        search_row.Add(self._btn_clear_search)
        root.Add(search_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        self._notebook = wx.Notebook(self)
        self._sections_page = wx.Panel(self._notebook)
        self._sections_scroll = wx.ScrolledWindow(self._sections_page, style=wx.VSCROLL)
        self._sections_scroll.SetScrollRate(0, 12)
        self._sections_content = wx.BoxSizer(wx.VERTICAL)
        self._sections_scroll.SetSizer(self._sections_content)
        sections_sizer = wx.BoxSizer(wx.VERTICAL)
        sections_sizer.Add(self._sections_scroll, proportion=1, flag=wx.EXPAND)
        self._sections_page.SetSizer(sections_sizer)

        self._json_page = wx.Panel(self._notebook)
        self._json_view = wx.TextCtrl(self._json_page, style=wx.TE_MULTILINE | wx.TE_READONLY)
        json_sizer = wx.BoxSizer(wx.VERTICAL)
        json_sizer.Add(self._json_view, proportion=1, flag=wx.EXPAND)
        self._json_page.SetSizer(json_sizer)

        self._notebook.AddPage(self._sections_page, "Sections")
        self._notebook.AddPage(self._json_page, "Advanced JSON")
        root.Add(self._notebook, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_reload = wx.Button(self, label="Reload")
        self._btn_save = wx.Button(self, label="Save")
        btn_row.Add(self._btn_reload, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_save, flag=wx.RIGHT, border=6)
        btn_row.AddStretchSpacer()
        root.Add(btn_row, flag=wx.EXPAND | wx.ALL, border=8)

        self._status = wx.StaticText(self, label="")
        root.Add(self._status, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)
        self.SetSizer(root)

        self._search.Bind(wx.EVT_TEXT, self._on_search)
        self._btn_clear_search.Bind(wx.EVT_BUTTON, self._on_clear_search)
        self._btn_reload.Bind(wx.EVT_BUTTON, self._on_reload)
        self._btn_save.Bind(wx.EVT_BUTTON, self._on_save)

        self._render_document()

    @property
    def view_model(self) -> EKMViewModel:
        return self._vm

    def confirm_discard(self) -> bool:
        if not self._vm.dirty:
            return True
        answer = wx.MessageBox(
            "Discard unsaved notebook edits?",
            "Unsaved changes",
            wx.YES_NO | wx.ICON_QUESTION,
        )
        return answer == wx.YES

    def _set_status(self, message: str) -> None:
        self._status.SetLabel(message)

    def _update_summary(self) -> None:
        info = self._vm.summary()
        counts = ", ".join(f"{k}={v}" for k, v in sorted(info["field_type_counts"].items()))
        dirty = " (unsaved changes)" if info["dirty"] else ""
        updated = info["updated_at"] or "not saved yet"
        filter_text = f" | Filter: {info['filter_query']!r}" if info.get("filter_query") else ""
        self._summary.SetLabel(
            f"Sections: {info['section_count']} | Fields: {counts or 'none'} | "
            f"Updated: {updated}{dirty}{filter_text}"
        )
        self._json_view.SetValue(
            json.dumps(self._vm.document.to_dict(), indent=2, ensure_ascii=False)
        )

    def _clear_sections(self) -> None:
        self._sections_content.Clear(True)
        self._section_widgets.clear()

    def _render_document(self) -> None:
        self._clear_sections()
        sections = self._vm.sections()
        if not sections:
            empty = wx.StaticText(
                self._sections_scroll,
                label="No engineering knowledge yet. Run AERF analysis and write conclusions to EKM.",
            )
            self._sections_content.Add(empty, flag=wx.ALL, border=8)
        else:
            container, widgets = build_sections_container(
                self._sections_scroll,
                sections,
                vm=self._vm,
                on_change=self._update_summary,
                on_status=self._set_status,
            )
            self._section_widgets = widgets
            self._sections_content.Add(container, flag=wx.EXPAND)
        self._sections_scroll.Layout()
        self._update_summary()
        self._set_status("Edit fields below, then Save to persist.")

    def _on_search(self, _event: wx.CommandEvent) -> None:
        self._vm.set_filter_query(self._search.GetValue())
        self._render_document()

    def _on_clear_search(self, _event: wx.CommandEvent) -> None:
        self._search.SetValue("")
        self._vm.set_filter_query(None)
        self._render_document()

    def _on_reload(self, _event: wx.CommandEvent) -> None:
        if self._vm.dirty:
            answer = wx.MessageBox(
                "Reload from disk and discard unsaved edits?",
                "Reload EKM",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            if answer != wx.YES:
                return
        self._vm.reload()
        self._render_document()

    def _on_save(self, _event: wx.CommandEvent) -> None:
        try:
            path = self._vm.save()
        except EKMError as exc:
            wx.MessageBox(str(exc), "Save failed", wx.OK | wx.ICON_ERROR)
            self._set_status(str(exc))
            return
        self._update_summary()
        self._set_status(f"Saved to {path}")
