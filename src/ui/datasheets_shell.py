"""Embeddable datasheets panel (wxPython) — missing parts, all required, reset & re-resolve."""

from __future__ import annotations

import threading
import webbrowser
from pathlib import Path

from context.datasheet_resolver import DatasheetResolution
from context.model import ProjectContext
from context.ai_datasheet_discovery import DiscoveryResult, format_fetch_attempts_summary
from ui.datasheet_supply import (
    MissingDatasheetRow,
    attach_datasheet_pdf,
    build_field_issue_rows_from_context,
    build_missing_rows_from_context,
    build_required_rows_from_context,
    format_row_detail_text,
    get_missing_datasheet_rows,
    get_required_datasheet_rows,
    get_symbol_field_issue_rows,
    manual_pdf_path_for_part,
    format_write_url_success_message,
    maybe_write_datasheet_urls_to_schematic,
    reset_datasheet_for_part,
    run_ai_discovery_for_rows,
)
from utils.config import load_config

try:
    import wx
except ImportError:  # pragma: no cover - wx only inside KiCad
    wx = None  # type: ignore[assignment]


if wx is not None:

    class _PdfDropTarget(wx.FileDropTarget):
        def __init__(self, shell: DatasheetsShell) -> None:
            super().__init__()
            self._shell = shell

        def OnDropFiles(self, x: int, y: int, filenames: list[str]) -> bool:
            pdfs = [Path(f) for f in filenames if f.lower().endswith(".pdf")]
            if not pdfs:
                return False
            row = self._shell._selected_row()
            if row is None:
                wx.MessageBox(
                    "Select a part row, then drop a PDF.",
                    "Attach PDF",
                    wx.OK | wx.ICON_INFORMATION,
                )
                return False
            self._shell._attach_pdf_path(row, pdfs[0])
            return True


    class _UrlApprovalDialog(wx.Dialog):
        """Let user pick a suggested URL for download."""

        def __init__(
            self,
            parent: wx.Window,
            part: str,
            urls: list[str],
        ) -> None:
            super().__init__(
                parent,
                title=f"Approve datasheet download — {part}",
                style=wx.DEFAULT_DIALOG_STYLE,
            )
            self._selected: str | None = None
            panel = wx.Panel(self)
            vbox = wx.BoxSizer(wx.VERTICAL)
            vbox.Add(
                wx.StaticText(
                    panel,
                    label=(
                        "AI suggested these HTTPS URLs. Select one to try downloading.\n"
                        "If automated download fails (e.g. bot protection), you can open "
                        "a URL in your browser and use Attach PDF…"
                    ),
                ),
                flag=wx.ALL,
                border=10,
            )
            self._radio = wx.RadioBox(
                panel,
                choices=urls,
                style=wx.RA_SPECIFY_ROWS,
            )
            if urls:
                self._radio.SetSelection(0)
            vbox.Add(self._radio, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
            btn_row = wx.BoxSizer(wx.HORIZONTAL)
            btn_download = wx.Button(panel, wx.ID_OK, "Download")
            btn_skip = wx.Button(panel, wx.ID_CANCEL, "Skip")
            btn_row.Add(btn_download, flag=wx.RIGHT, border=6)
            btn_row.Add(btn_skip)
            vbox.Add(btn_row, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
            panel.SetSizer(vbox)
            outer = wx.BoxSizer(wx.VERTICAL)
            outer.Add(panel, proportion=1, flag=wx.EXPAND)
            self.SetSizer(outer)
            self.Bind(wx.EVT_BUTTON, self._on_download, btn_download)
            self.Bind(wx.EVT_BUTTON, self._on_skip, btn_skip)
            self.Fit()

        def _on_download(self, _event: wx.CommandEvent) -> None:
            idx = self._radio.GetSelection()
            if idx >= 0:
                self._selected = self._radio.GetString(idx)
            self.EndModal(wx.ID_OK)

        def _on_skip(self, _event: wx.CommandEvent) -> None:
            self._selected = None
            self.EndModal(wx.ID_CANCEL)

        @property
        def selected_url(self) -> str | None:
            return self._selected


    class _FetchReportDialog(wx.Dialog):
        """Show per-URL download results and let the user open a URL manually."""

        def __init__(
            self,
            parent: wx.Window,
            results: list[DiscoveryResult],
        ) -> None:
            super().__init__(
                parent,
                title="Datasheet download report",
                style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                size=(720, 420),
            )
            panel = wx.Panel(self)
            vbox = wx.BoxSizer(wx.VERTICAL)
            intro = wx.StaticText(
                panel,
                label=(
                    "Automated download did not succeed for the part(s) below. "
                    "Sites often block scripted downloads — select a URL and open it "
                    "in your browser, save the PDF, then use Attach PDF… in the "
                    "Datasheets panel."
                ),
            )
            intro.Wrap(680)
            vbox.Add(intro, flag=wx.ALL, border=10)

            self._list = wx.ListCtrl(
                panel,
                style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN,
            )
            self._list.InsertColumn(0, "Part", width=90)
            self._list.InsertColumn(1, "URL", width=360)
            self._list.InsertColumn(2, "Result", width=220)
            self._rows: list[tuple[str, str, str]] = []
            row_idx = 0
            for result in results:
                tried = {url: err for url, err in result.fetch_attempts}
                urls = list(result.suggested_urls) or list(tried.keys())
                if not urls and result.selected_url:
                    urls = [result.selected_url]
                seen: set[str] = set()
                for url in urls:
                    if url in seen:
                        continue
                    seen.add(url)
                    if url in tried:
                        err = tried[url]
                        status = "Downloaded" if err is None else f"Failed: {err}"
                    else:
                        status = "Not attempted"
                    self._rows.append((result.part, url, status))
                    self._list.InsertItem(row_idx, result.part)
                    self._list.SetItem(row_idx, 1, url[:120])
                    self._list.SetItem(row_idx, 2, status[:100])
                    row_idx += 1
            vbox.Add(self._list, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

            btn_row = wx.BoxSizer(wx.HORIZONTAL)
            btn_open = wx.Button(panel, label="Open URL in browser")
            btn_copy = wx.Button(panel, label="Copy URL")
            btn_close = wx.Button(panel, wx.ID_CLOSE, label="Close")
            btn_row.Add(btn_open, flag=wx.RIGHT, border=6)
            btn_row.Add(btn_copy, flag=wx.RIGHT, border=6)
            btn_row.AddStretchSpacer()
            btn_row.Add(btn_close)
            vbox.Add(btn_row, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
            panel.SetSizer(vbox)
            outer = wx.BoxSizer(wx.VERTICAL)
            outer.Add(panel, proportion=1, flag=wx.EXPAND)
            self.SetSizer(outer)
            self.Bind(wx.EVT_BUTTON, self._on_open, btn_open)
            self.Bind(wx.EVT_BUTTON, self._on_copy, btn_copy)
            self.Bind(wx.EVT_BUTTON, lambda _e: self.EndModal(wx.ID_CLOSE), btn_close)
            if self._rows:
                self._list.Select(0)
            self.CentreOnParent()

        def _selected(self) -> tuple[str, str, str] | None:
            idx = self._list.GetFirstSelected()
            if idx < 0 or idx >= len(self._rows):
                return None
            return self._rows[idx]

        def _on_open(self, _event: wx.CommandEvent) -> None:
            row = self._selected()
            if row is None:
                return
            webbrowser.open(row[1])

        def _on_copy(self, _event: wx.CommandEvent) -> None:
            row = self._selected()
            if row is None:
                return
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(row[1]))
                wx.TheClipboard.Close()


    class _ResetConfirmDialog(wx.Dialog):
        """Confirm per-part datasheet reset."""

        def __init__(
            self,
            parent: wx.Window,
            part: str,
            reference_count: int,
        ) -> None:
            super().__init__(
                parent,
                title=f"Reset datasheet — {part}",
                style=wx.DEFAULT_DIALOG_STYLE,
            )
            self.delete_orphan = False
            panel = wx.Panel(self)
            vbox = wx.BoxSizer(wx.VERTICAL)
            msg = (
                f"Clear cached PDF links for {part} ({reference_count} ref(s)) "
                "and re-run URL fetch / AI discovery?\n\n"
                "Local datasheets/{Value}.pdf will be moved to .quarantine/."
            )
            label = wx.StaticText(panel, label=msg)
            label.Wrap(480)
            vbox.Add(label, flag=wx.ALL, border=10)
            self._chk_delete = wx.CheckBox(
                panel,
                label="Delete orphaned PDF from shared library if no other project uses it",
            )
            vbox.Add(self._chk_delete, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
            btn_row = wx.BoxSizer(wx.HORIZONTAL)
            btn_ok = wx.Button(panel, wx.ID_OK, "Reset & re-resolve")
            btn_cancel = wx.Button(panel, wx.ID_CANCEL, "Cancel")
            btn_row.Add(btn_ok, flag=wx.RIGHT, border=6)
            btn_row.Add(btn_cancel)
            vbox.Add(btn_row, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
            panel.SetSizer(vbox)
            outer = wx.BoxSizer(wx.VERTICAL)
            outer.Add(panel, proportion=1, flag=wx.EXPAND)
            self.SetSizer(outer)
            self.Bind(wx.EVT_BUTTON, self._on_ok, btn_ok)
            self.Bind(wx.EVT_BUTTON, self._on_cancel, btn_cancel)
            self.Fit()

        def _on_ok(self, _event: wx.CommandEvent) -> None:
            self.delete_orphan = self._chk_delete.GetValue()
            self.EndModal(wx.ID_OK)

        def _on_cancel(self, _event: wx.CommandEvent) -> None:
            self.EndModal(wx.ID_CANCEL)


class DatasheetsShell(wx.Panel):
    """Embeddable panel for datasheet-required parts (missing and all required tabs)."""

    def __init__(
        self,
        parent: wx.Window,
        project_path: Path,
        *,
        embedded: bool = False,
        retry_failed_urls: bool = False,
        force_refresh_urls: bool = False,
        ai_datasheets: bool = False,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for DatasheetsShell")
        super().__init__(parent)
        self._embedded = embedded
        self._project_path = project_path.expanduser().resolve()
        self._retry_failed_urls = retry_failed_urls
        self._force_refresh_urls = force_refresh_urls
        self._cfg = load_config()
        self._rows_missing: list[MissingDatasheetRow] = []
        self._rows_all: list[MissingDatasheetRow] = []
        self._rows_field: list[MissingDatasheetRow] = []
        self._ai_enabled = ai_datasheets
        self._ai_cost_warned = ai_datasheets
        self._row_status: dict[str, str] = {}
        self._busy = False
        self._cancel_requested = threading.Event()
        self._worker: threading.Thread | None = None
        self._discovery_detail_lines: list[str] = []

        root = wx.BoxSizer(wx.VERTICAL)

        intro = wx.StaticText(
            self,
            label=(
                "Manage datasheet PDFs for SUBCKT / detailed analysis. "
                "Attach, reset stale links, or use AI discovery. "
                f"Manual path: {manual_pdf_path_for_part(self._cfg.artifact_library_path, '<Value>')}"
            ),
        )
        intro.Wrap(780)
        root.Add(intro, flag=wx.ALL | wx.EXPAND, border=10)

        self._chk_ai = wx.CheckBox(
            self,
            label="Use AI to find datasheets (Anthropic API — may incur cost)",
        )
        self._chk_ai.SetValue(ai_datasheets)
        root.Add(self._chk_ai, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        self._notebook = wx.Notebook(self)
        self._list_missing = self._make_list_ctrl(self._notebook)
        self._list_all = self._make_list_ctrl(self._notebook, include_pdf_column=True)

        self._field_tab = wx.Panel(self._notebook)
        field_tab_sizer = wx.BoxSizer(wx.VERTICAL)
        field_intro = wx.StaticText(
            self._field_tab,
            label=(
                "Parts whose symbol Datasheet property is empty, a local path, "
                "or an HTTPS URL that failed or differs from the resolved PDF URL."
            ),
        )
        field_intro.Wrap(760)
        field_tab_sizer.Add(field_intro, flag=wx.ALL | wx.EXPAND, border=8)
        self._chk_write_url = wx.CheckBox(
            self._field_tab,
            label="After reset / attach / write: update symbol Datasheet with resolved HTTPS URL",
        )
        self._chk_write_url.SetValue(self._cfg.datasheet_write_symbol_url)
        field_tab_sizer.Add(self._chk_write_url, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)
        self._list_field = self._make_list_ctrl(
            self._field_tab,
            include_field_columns=True,
        )
        field_tab_sizer.Add(self._list_field, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)
        self._field_tab.SetSizer(field_tab_sizer)

        self._notebook.AddPage(self._list_missing, "Missing")
        self._notebook.AddPage(self._list_all, "All required")
        self._notebook.AddPage(self._field_tab, "Symbol field")
        self._list_missing.SetDropTarget(_PdfDropTarget(self))
        self._list_all.SetDropTarget(_PdfDropTarget(self))
        self._list_field.SetDropTarget(_PdfDropTarget(self))
        for lst in (self._list_missing, self._list_all, self._list_field):
            lst.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_row_selected)
            lst.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self._on_row_context_menu)
        root.Add(self._notebook, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        self._footer = wx.Panel(self, style=wx.BORDER_NONE)
        footer_sizer = wx.BoxSizer(wx.VERTICAL)

        status_box = wx.StaticBox(self._footer, label="Status")
        status_inner = wx.StaticBoxSizer(status_box, wx.VERTICAL)
        self._status = wx.StaticText(
            self._footer,
            label="Loading datasheet list…",
        )
        self._status_detail = wx.TextCtrl(
            self._footer,
            value="Progress and results appear here during reset, fetch, and AI discovery.",
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP | wx.BORDER_NONE,
            size=(-1, 64),
        )
        self._status_detail.SetBackgroundColour(self._footer.GetBackgroundColour())
        self._status_detail.SetForegroundColour(wx.Colour(80, 80, 80))
        self._status_detail.SetMaxSize((-1, 88))
        status_inner.Add(self._status, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=6)
        status_inner.Add(
            self._status_detail,
            proportion=0,
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            border=6,
        )
        footer_sizer.Add(status_inner, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=8)

        self._gauge = wx.Gauge(self._footer, range=100, style=wx.GA_HORIZONTAL)
        self._gauge.Hide()
        footer_sizer.Add(self._gauge, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_attach = wx.Button(self._footer, label="Attach PDF…")
        self._btn_reset = wx.Button(self._footer, label="Reset & re-resolve…")
        self._btn_ai = wx.Button(self._footer, label="Find with AI")
        self._btn_open_url = wx.Button(self._footer, label="Open URL")
        self._btn_copy_path = wx.Button(self._footer, label="Copy manual path")
        self._btn_write_url = wx.Button(self._footer, label="Write URL to schematic")
        btn_row.Add(self._btn_attach, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_reset, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_ai, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_open_url, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_copy_path, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_write_url, flag=wx.RIGHT, border=6)
        footer_sizer.Add(btn_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=8)

        footer_sizer.AddSpacer(12)

        btn_row2 = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_refresh = wx.Button(self._footer, label="Refresh")
        self._btn_force = wx.Button(self._footer, label="Force refresh all URLs")
        self._btn_cancel = wx.Button(self._footer, label="Cancel")
        self._btn_cancel.Hide()
        self._btn_close = wx.Button(self._footer, wx.ID_CLOSE, label="Close")
        btn_row2.Add(self._btn_refresh, flag=wx.RIGHT, border=6)
        btn_row2.Add(self._btn_force, flag=wx.RIGHT, border=6)
        btn_row2.Add(self._btn_cancel, flag=wx.RIGHT, border=6)
        btn_row2.AddStretchSpacer()
        if not self._embedded:
            btn_row2.Add(self._btn_close)
        footer_sizer.Add(btn_row2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        self._footer.SetSizer(footer_sizer)
        root.Add(self._footer, proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=4)

        self.SetSizer(root)

        self.SetMinSize((840, 640))

        self._btn_attach.Bind(wx.EVT_BUTTON, self._on_attach)
        self._btn_reset.Bind(wx.EVT_BUTTON, self._on_reset)
        self._btn_ai.Bind(wx.EVT_BUTTON, self._on_find_ai)
        self._btn_open_url.Bind(wx.EVT_BUTTON, self._on_open_url)
        self._btn_copy_path.Bind(wx.EVT_BUTTON, self._on_copy_path)
        self._btn_write_url.Bind(wx.EVT_BUTTON, self._on_write_url)
        self._btn_refresh.Bind(wx.EVT_BUTTON, self._on_refresh)
        self._btn_force.Bind(wx.EVT_BUTTON, self._on_force_refresh)
        self._btn_cancel.Bind(wx.EVT_BUTTON, self._on_cancel)
        self._btn_close.Bind(wx.EVT_BUTTON, self._on_close)
        self._chk_ai.Bind(wx.EVT_CHECKBOX, self._on_ai_toggle)
        self._chk_write_url.Bind(wx.EVT_CHECKBOX, self._on_write_url_toggle)
        self._update_ai_button_state()
        self._refresh_rows()
        self._layout_panel()

    def _action_buttons(self) -> list[wx.Button]:
        return [
            self._btn_attach,
            self._btn_reset,
            self._btn_ai,
            self._btn_open_url,
            self._btn_copy_path,
            self._btn_write_url,
            self._btn_refresh,
            self._btn_force,
            self._btn_cancel,
            self._btn_close,
        ]

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        for btn in self._action_buttons():
            if btn in (self._btn_close, self._btn_cancel):
                continue
            btn.Enable(not busy)
        self._btn_cancel.Show() if busy else self._btn_cancel.Hide()
        self._btn_cancel.Enable(busy)
        if busy:
            self._gauge.Show()
            self._gauge.Pulse()
        else:
            self._gauge.Hide()
            self._cancel_requested.clear()
        if not busy:
            self._update_ai_button_state()
            if not self._rows_missing:
                self._btn_attach.Enable(False)
        self._layout_panel()

    def _on_cancel(self, _event: wx.CommandEvent) -> None:
        if not self._busy:
            return
        self._cancel_requested.set()
        self._set_status("Cancelling…", "Finishing the current step, then stopping.")

    def _layout_panel(self) -> None:
        self._footer.Layout()
        self.Layout()
        self.GetTopLevelParent().Layout()
        self._footer.Refresh()
        self.Refresh()
        self.GetTopLevelParent().Refresh()

    def _set_status(self, main: str, detail: str = "") -> None:
        self._status.SetLabel(main)
        detail_text = detail if detail else " "
        self._status_detail.SetValue(detail_text)
        self._layout_panel()
        try:
            wx.YieldIfNeeded()
        except AttributeError:
            wx.SafeYield()

    def _append_discovery_detail(self, line: str) -> None:
        self._discovery_detail_lines.append(line)
        # Keep last ~40 lines visible in the status panel during long runs.
        text = "\n".join(self._discovery_detail_lines[-40:])
        self._status_detail.SetValue(text)
        self._layout_panel()
        try:
            wx.YieldIfNeeded()
        except AttributeError:
            wx.SafeYield()

    def _on_fetch_attempt(self, part: str, url: str, error: str | None) -> None:
        if error is None:
            line = f"{part}: OK — {url}"
            self._row_status[part] = "Downloaded"
        else:
            short = error if len(error) <= 80 else error[:77] + "…"
            line = f"{part}: FAIL — {url}\n         {short}"
            self._row_status[part] = f"Failed ({short[:30]})"
        self._append_discovery_detail(line)
        self._repaint_list_status()

    def _resolution_for_part(self, ctx: ProjectContext, part: str) -> DatasheetResolution | None:
        part_norm = part.strip()
        for sym in ctx.symbols:
            if (sym.value or sym.reference).strip() != part_norm:
                continue
            res = ctx.datasheet_resolutions.get(sym.reference)
            if res is not None:
                return res
        return None

    def _show_reset_outcome(self, ctx: ProjectContext, part: str) -> None:
        res = self._resolution_for_part(ctx, part)
        discovery = ctx.ai_discovery_results.get(part) if ctx.ai_discovery_results else None

        if res is not None and res.status == "resolved":
            pdf_name = Path(res.local_path).name if res.local_path else (res.artifact_id or "PDF")
            via = "cache"
            if res.sources_tried:
                if "https_fetch" in res.sources_tried:
                    via = "URL download"
                elif discovery is not None and discovery.outcome == "downloaded":
                    via = "AI discovery + download"
                elif "symbol_datasheet_local" in res.sources_tried:
                    via = "symbol local path"
                elif "user_attach" in res.sources_tried:
                    via = "attached PDF"
            self._set_status(f"{part}: resolved ({via}).", f"PDF: {pdf_name}")
            self._row_status[part] = "resolved"
        elif discovery is not None:
            err = discovery.error or ""
            if discovery.fetch_attempts:
                detail = format_fetch_attempts_summary(
                    discovery.fetch_attempts,
                    suggested_urls=discovery.suggested_urls,
                )
            else:
                detail = f"AI outcome: {discovery.outcome}"
                if err:
                    detail += f" — {err}"
                if discovery.suggested_urls:
                    detail += f" | Suggested: {discovery.suggested_urls[0][:80]}"
            self._set_status(f"{part}: not resolved after reset.", detail)
            self._row_status[part] = str(discovery.outcome)
        elif res is not None:
            err = ""
            for src in res.sources_tried:
                if src.startswith("fetch_error:"):
                    err = src.replace("fetch_error:", "", 1)
                    break
            detail = err or "No PDF found — attach manually or set an HTTPS URL on the symbol."
            self._set_status(f"{part}: {res.status}.", detail)
            self._row_status[part] = res.status
        else:
            self._set_status(f"{part}: reset finished.", "No resolution data returned.")
        self._repaint_list_status()

    def _make_list_ctrl(
        self,
        parent: wx.Window,
        *,
        include_pdf_column: bool = False,
        include_field_columns: bool = False,
    ) -> wx.ListCtrl:
        lst = wx.ListCtrl(
            parent,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN,
        )
        lst.InsertColumn(0, "Part (Value)", width=130)
        lst.InsertColumn(1, "Refs", width=45)
        lst.InsertColumn(2, "Status", width=120)
        if include_field_columns:
            lst.InsertColumn(3, "Symbol field", width=200)
            lst.InsertColumn(4, "Resolved URL", width=220)
            lst.InsertColumn(5, "Detail", width=200)
        elif include_pdf_column:
            lst.InsertColumn(3, "PDF / source", width=220)
            lst.InsertColumn(4, "Detail", width=240)
        else:
            lst.InsertColumn(3, "Error / URL", width=380)
        return lst

    def _active_list(self) -> wx.ListCtrl:
        sel = self._notebook.GetSelection()
        if sel == 0:
            return self._list_missing
        if sel == 1:
            return self._list_all
        return self._list_field

    def _active_rows(self) -> list[MissingDatasheetRow]:
        sel = self._notebook.GetSelection()
        if sel == 0:
            return self._rows_missing
        if sel == 1:
            return self._rows_all
        return self._rows_field

    def confirm_close(self) -> bool:
        if not self._busy:
            return True
        if wx.MessageBox(
            "A datasheet operation is still running.\n\nCancel it and close?",
            "Datasheets",
            wx.YES_NO | wx.ICON_WARNING,
        ) != wx.YES:
            return False
        self._cancel_requested.set()
        return True

    def _on_close(self, _event: wx.CommandEvent) -> None:
        top = self.GetTopLevelParent()
        if hasattr(top, "EndModal"):
            top.EndModal(wx.ID_OK)

    def _on_ai_toggle(self, _event: wx.CommandEvent) -> None:
        enabled = self._chk_ai.GetValue()
        if enabled and not self._ai_cost_warned:
            if wx.MessageBox(
                "AI datasheet discovery sends symbol context to Anthropic and may incur API cost.\n\n"
                "Continue?",
                "Enable AI discovery",
                wx.YES_NO | wx.ICON_QUESTION,
            ) != wx.YES:
                self._chk_ai.SetValue(False)
                return
            self._ai_cost_warned = True
        self._ai_enabled = self._chk_ai.GetValue()
        self._update_ai_button_state()

    def _on_row_selected(self, event: wx.ListEvent) -> None:
        rows = self._active_rows()
        idx = event.GetIndex()
        if 0 <= idx < len(rows):
            self._show_row_detail(rows[idx])
        event.Skip()

    def _on_row_context_menu(self, event: wx.ListEvent) -> None:
        lst = event.GetEventObject()
        if not isinstance(lst, wx.ListCtrl):
            return
        idx = event.GetIndex()
        rows = self._active_rows()
        if idx < 0 or idx >= len(rows):
            return
        row = rows[idx]
        lst.Select(idx)
        self._show_row_detail(row)
        menu = wx.Menu()
        copy_detail = menu.Append(wx.ID_COPY, "Copy detail text")
        copy_url = menu.Append(wx.ID_ANY, "Copy suggested URL")
        copy_url_id = copy_url.GetId()
        copy_url.Enable(bool(row.suggested_urls or row.selected_url or row.symbol_datasheet_url))
        lst.PopupMenu(menu)
        selected = menu.GetPopupMenuSelection()
        if selected == copy_detail.GetId():
            self._copy_text_to_clipboard(format_row_detail_text(row))
        elif selected == copy_url_id:
            url = row.selected_url or (row.suggested_urls[0] if row.suggested_urls else None)
            if url is None:
                url = row.symbol_datasheet_url
            if url:
                self._copy_text_to_clipboard(url)
        menu.Destroy()

    def _copy_text_to_clipboard(self, text: str) -> None:
        if not text:
            return
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()
            preview = text[:120] + ("…" if len(text) > 120 else "")
            self._set_status("Copied to clipboard.", preview)

    def _show_row_detail(self, row: MissingDatasheetRow) -> None:
        detail = format_row_detail_text(row)
        if detail:
            self._set_status(f"{row.part} — {row.discovery_status or row.status}", detail)
        else:
            self._set_status(
                f"{row.part} — {row.discovery_status or row.status}",
                "No extra detail for this row.",
            )

    def _on_write_url_toggle(self, _event: wx.CommandEvent) -> None:
        self._cfg.datasheet_write_symbol_url = self._chk_write_url.GetValue()

    def _update_ai_button_state(self) -> None:
        self._btn_ai.Enable(self._ai_enabled and bool(self._rows_missing))

    def _on_refresh(self, _event: wx.CommandEvent) -> None:
        self._force_refresh_urls = False
        self._row_status.clear()
        self._refresh_rows()

    def _on_force_refresh(self, _event: wx.CommandEvent) -> None:
        if self._busy:
            return
        self._force_refresh_urls = True
        self._set_status(
            "Force refreshing all HTTPS datasheet URLs (full catalog bypass)…",
            "Re-fetches every symbol HTTPS URL; does not affect parts without HTTPS fields.",
        )
        self._row_status.clear()
        self._refresh_rows()
        self._force_refresh_urls = False

    def _selected_row(self) -> MissingDatasheetRow | None:
        lst = self._active_list()
        rows = self._active_rows()
        idx = lst.GetFirstSelected()
        if idx == -1 or idx >= len(rows):
            return None
        return rows[idx]

    def _approve_url_dialog(self, part: str, urls: list[str]) -> str | None:
        """Show URL approval on the wx main thread (required inside KiCad)."""
        self._row_status[part] = "Choose AI URL…"
        self._repaint_list_status()
        self._set_status(
            f"{part}: AI found URL(s).",
            "Select a URL to download, or Cancel to skip.",
        )
        dlg = _UrlApprovalDialog(self.GetTopLevelParent(), part, urls)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                return dlg.selected_url
        finally:
            dlg.Destroy()
        return None

    def _approve_url_thread_safe(self, part: str, urls: list[str]) -> str | None:
        """Run URL approval on the wx main thread from a worker thread."""
        holder: list[str | None] = []
        done = threading.Event()

        def on_main() -> None:
            try:
                holder.append(self._approve_url_dialog(part, urls))
            finally:
                done.set()

        wx.CallAfter(on_main)
        while not done.wait(timeout=0.05):
            if self._cancel_requested.is_set():
                return None
        return holder[0] if holder else None

    def _set_row_status(self, part: str, status: str) -> None:
        self._row_status[part] = status
        self._repaint_list_status()

    def _repaint_list_status(self) -> None:
        for lst, rows, mode in (
            (self._list_missing, self._rows_missing, "missing"),
            (self._list_all, self._rows_all, "all"),
            (self._list_field, self._rows_field, "field"),
        ):
            for i, row in enumerate(rows):
                if mode == "field":
                    status = self._row_status.get(row.part) or row.field_issue_label or row.status
                else:
                    status = self._row_status.get(row.part) or row.discovery_status or row.status
                lst.SetItem(i, 2, status)

    def _on_reset(self, _event: wx.CommandEvent) -> None:
        if self._busy:
            return
        row = self._selected_row()
        if row is None:
            wx.MessageBox(
                "Select a part row first.",
                "Reset datasheet",
                wx.OK | wx.ICON_INFORMATION,
            )
            return
        dlg = _ResetConfirmDialog(self.GetTopLevelParent(), row.part, row.reference_count)
        if dlg.ShowModal() != wx.ID_OK:
            return
        delete_orphan = dlg.delete_orphan
        part = row.part
        rerun_ai = self._ai_enabled

        self._set_busy(True)
        self._set_status(f"Resetting {part}…", "Clearing cache and re-resolving.")
        self._row_status[part] = "Resetting…"
        self._repaint_list_status()
        self._cancel_requested.clear()
        self._worker = threading.Thread(
            target=self._run_reset_worker,
            args=(part, delete_orphan, rerun_ai),
            daemon=True,
        )
        self._worker.start()

    def _run_reset_worker(self, part: str, delete_orphan: bool, rerun_ai: bool) -> None:
        def on_status(message: str) -> None:
            wx.CallAfter(self._set_status, f"Resetting {part}…", message)
            if "AI" in message or "Download" in message or "approval" in message.lower():
                wx.CallAfter(self._set_row_status, part, message[:40])

        try:
            ctx = reset_datasheet_for_part(
                self._project_path,
                part,
                config=self._cfg,
                delete_orphan_artifact=delete_orphan,
                rerun_ai_discovery=rerun_ai,
                approve_ai_datasheet_url=(
                    self._approve_url_thread_safe if rerun_ai else None
                ),
                on_status=on_status,
                verbose=False,
            )
            wx.CallAfter(self._on_reset_finished, ctx, part, None)
        except Exception as exc:  # noqa: BLE001
            wx.CallAfter(self._on_reset_finished, None, part, exc)

    def _on_reset_finished(
        self,
        ctx: ProjectContext | None,
        part: str,
        exc: Exception | None,
    ) -> None:
        try:
            if exc is not None:
                self._set_status(f"Reset failed for {part}.", str(exc))
                self._row_status[part] = "reset failed"
                self._repaint_list_status()
                wx.MessageBox(
                    f"Reset failed:\n{exc}",
                    "Reset datasheet",
                    wx.OK | wx.ICON_ERROR,
                )
            elif ctx is not None:
                self._show_reset_outcome(ctx, part)
                self._refresh_rows(preserve_status=True)
        finally:
            self._worker = None
            self._set_busy(False)
    def _on_find_ai(self, _event: wx.CommandEvent) -> None:
        if not self._ai_enabled or self._busy:
            return
        row = self._selected_row()
        only_parts: set[str] | None = {row.part} if row else None
        if only_parts:
            scope = f"selected part ({row.part})"
        else:
            scope = "all missing parts"
            if wx.MessageBox(
                "No row selected — Find with AI will run for every missing part.\n\n"
                "Select a row first to search only that Value.\n\nContinue for all?",
                "AI datasheet discovery",
                wx.YES_NO | wx.ICON_QUESTION,
            ) != wx.YES:
                return
        if not self._cfg.datasheet_ai_discovery_auto_fetch:
            if wx.MessageBox(
                f"Find with AI will suggest datasheet URLs for {scope} "
                "and ask you to approve each download.\n\nContinue?",
                "AI datasheet discovery",
                wx.YES_NO | wx.ICON_QUESTION,
            ) != wx.YES:
                return
        self._set_busy(True)
        self._discovery_detail_lines = []
        self._set_status(
            "Running AI datasheet discovery…",
            f"Working on {scope} — each URL attempt is logged below.",
        )
        if only_parts:
            for part in only_parts:
                self._row_status[part] = "Searching…"
        else:
            for missing_row in self._rows_missing:
                self._row_status[missing_row.part] = "Searching…"
        self._repaint_list_status()
        self._cancel_requested.clear()
        self._worker = threading.Thread(
            target=self._run_ai_discovery_worker,
            args=(only_parts,),
            daemon=True,
        )
        self._worker.start()

    def _run_ai_discovery_worker(self, only_parts: set[str] | None) -> None:
        try:
            ctx = run_ai_discovery_for_rows(
                self._project_path,
                config=self._cfg,
                only_parts=only_parts,
                should_cancel=self._cancel_requested.is_set,
                approve_ai_datasheet_url=self._approve_url_thread_safe,
                on_part_status=lambda part, st: wx.CallAfter(self._set_row_status, part, st),
                on_fetch_attempt=lambda part, url, err: wx.CallAfter(
                    self._on_fetch_attempt, part, url, err
                ),
                verbose=False,
            )
            wx.CallAfter(self._on_ai_discovery_finished, ctx, None)
        except Exception as exc:  # noqa: BLE001
            wx.CallAfter(self._on_ai_discovery_finished, None, exc)

    def _on_ai_discovery_finished(
        self,
        ctx: ProjectContext | None,
        exc: Exception | None,
    ) -> None:
        try:
            if exc is not None:
                self._set_status("AI discovery failed.", str(exc))
                wx.MessageBox(
                    f"AI discovery failed:\n{exc}",
                    "AI discovery",
                    wx.OK | wx.ICON_ERROR,
                )
            elif ctx is not None:
                self.apply_context_rows(ctx)
                downloaded = sum(
                    1
                    for r in ctx.ai_discovery_results.values()
                    if getattr(r, "outcome", None) == "downloaded"
                )
                failed_results = [
                    r
                    for r in ctx.ai_discovery_results.values()
                    if getattr(r, "outcome", None) == "fetch_failed"
                ]
                cancelled = self._cancel_requested.is_set()
                detail_lines = list(self._discovery_detail_lines)
                if not detail_lines and failed_results:
                    for result in failed_results:
                        detail_lines.append(
                            format_fetch_attempts_summary(
                                result.fetch_attempts,
                                suggested_urls=result.suggested_urls,
                            )
                        )
                detail = f"{downloaded} part(s) downloaded."
                if cancelled:
                    detail += " Cancelled before completion."
                if failed_results:
                    detail += (
                        f" {len(failed_results)} part(s) failed automated download — "
                        "see report dialog."
                    )
                self._set_status("AI discovery finished.", detail)
                if detail_lines:
                    self._status_detail.SetValue("\n".join(detail_lines[-40:]))
                if failed_results:
                    dlg = _FetchReportDialog(self.GetTopLevelParent(), failed_results)
                    try:
                        dlg.ShowModal()
                    finally:
                        dlg.Destroy()
        finally:
            self._row_status.clear()
            self._worker = None
            self._set_busy(False)

    def _on_open_url(self, _event: wx.CommandEvent) -> None:
        row = self._selected_row()
        if row is None:
            wx.MessageBox("Select a part row first.", "Open URL", wx.OK | wx.ICON_INFORMATION)
            return
        url = row.selected_url or row.symbol_datasheet_url
        if not url and row.suggested_urls:
            url = row.suggested_urls[0]
        if not url:
            wx.MessageBox("No URL available for this row.", "Open URL", wx.OK | wx.ICON_INFORMATION)
            return
        webbrowser.open(url)

    def _on_write_url(self, _event: wx.CommandEvent) -> None:
        if self._busy:
            return
        row = self._selected_row()
        if row is None:
            wx.MessageBox(
                "Select a resolved part row first.",
                "Write URL to schematic",
                wx.OK | wx.ICON_INFORMATION,
            )
            return
        ctx, _rows = get_required_datasheet_rows(self._project_path, config=self._cfg, verbose=False)
        part_resolved = any(
            (sym.value or sym.reference).strip() == row.part.strip()
            and ctx.datasheet_resolutions.get(sym.reference)
            and ctx.datasheet_resolutions[sym.reference].status == "resolved"
            for sym in ctx.symbols
        )
        if not part_resolved and not row.resolved_url:
            wx.MessageBox(
                f"{row.part} is not resolved yet — attach or fetch a PDF first.",
                "Write URL to schematic",
                wx.OK | wx.ICON_INFORMATION,
            )
            return
        from context.artifacts.store import ArtifactStore

        store = ArtifactStore(self._cfg.artifact_library_path)
        prev = self._cfg.datasheet_write_symbol_url
        self._cfg.datasheet_write_symbol_url = True
        try:
            result = maybe_write_datasheet_urls_to_schematic(
                self._project_path,
                ctx,
                store,
                config=self._cfg,
                part=row.part,
            )
        finally:
            self._cfg.datasheet_write_symbol_url = prev
        if result is None or result.changed_count == 0:
            detail = (
                result.skipped[0]
                if result and result.skipped
                else "No HTTPS URL available for this part."
            )
            self._set_status(f"Could not write URL for {row.part}.", detail)
            wx.MessageBox(
                f"No schematic Datasheet field was updated.\n\n{detail}",
                "Write URL to schematic",
                wx.OK | wx.ICON_INFORMATION,
            )
            return
        refs = ", ".join(u.reference for u in result.updated)
        url = result.updated[0].new_url
        self._set_status(
            f"Updated Datasheet for {row.part} ({refs}).",
            url[:120],
        )
        wx.MessageBox(
            format_write_url_success_message(result),
            "Write URL to schematic",
            wx.OK | wx.ICON_INFORMATION,
        )

    def _on_copy_path(self, _event: wx.CommandEvent) -> None:
        row = self._selected_row()
        if row is None:
            wx.MessageBox(
                "Select a part row first.",
                "Copy manual path",
                wx.OK | wx.ICON_INFORMATION,
            )
            return
        path = str(manual_pdf_path_for_part(self._cfg.artifact_library_path, row.part))
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(path))
            wx.TheClipboard.Close()
        self._set_status(f"Copied manual path for {row.part}.", path)

    def _on_attach(self, _event: wx.CommandEvent) -> None:
        row = self._selected_row()
        if row is None:
            wx.MessageBox(
                "Select a part row first.",
                "Attach PDF",
                wx.OK | wx.ICON_INFORMATION,
            )
            return
        with wx.FileDialog(
            self.GetTopLevelParent(),
            f"Attach datasheet PDF for {row.part}",
            wildcard="PDF files (*.pdf)|*.pdf",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            self._attach_pdf_path(row, Path(dlg.GetPath()))

    def _attach_pdf_path(self, row: MissingDatasheetRow, pdf_path: Path) -> None:
        try:
            ctx = attach_datasheet_pdf(
                self._project_path,
                row.part,
                pdf_path,
                config=self._cfg,
                verbose=False,
            )
        except (OSError, ValueError) as exc:
            wx.MessageBox(
                f"Could not attach PDF:\n{exc}",
                "Attach PDF",
                wx.OK | wx.ICON_ERROR,
            )
            return
        res = None
        for sym in ctx.symbols:
            if (sym.value or sym.reference).strip() == row.part.strip():
                res = ctx.datasheet_resolutions.get(sym.reference)
                if res is not None:
                    break
        library_path = ""
        if res is not None and res.local_path is not None:
            library_path = str(res.local_path)
        elif res is not None and res.status == "resolved":
            library_path = str(
                manual_pdf_path_for_part(self._cfg.artifact_library_path, row.part)
            )
        if res is not None and res.status == "resolved":
            self._set_status(
                f"{row.part}: attached and resolved.",
                f"Library copy: {library_path}",
            )
            self._row_status[row.part] = "resolved"
        else:
            self._set_status(
                f"Attach finished for {row.part}, but status is still {res.status if res else 'unknown'}.",
                "Try Refresh or check the All required tab for details.",
            )
        self._refresh_rows(preserve_status=True)

    def _detail_text(self, row: MissingDatasheetRow) -> str:
        return format_row_detail_text(row, max_length=200)

    def apply_context_rows(self, ctx: ProjectContext) -> None:
        """Update all tabs from a collected context without re-running AI discovery."""
        self._rows_missing = build_missing_rows_from_context(ctx, config=self._cfg)
        self._rows_all = build_required_rows_from_context(ctx, config=self._cfg)
        self._rows_field = build_field_issue_rows_from_context(ctx, config=self._cfg)
        self._populate_list(self._list_missing, self._rows_missing, include_pdf_column=False)
        self._populate_list(self._list_all, self._rows_all, include_pdf_column=True)
        self._populate_list(
            self._list_field,
            self._rows_field,
            include_field_columns=True,
        )
        self._update_ai_button_state()
        if not self._rows_missing:
            self._btn_attach.Enable(False)
            self._btn_ai.Enable(False)
        else:
            self._btn_attach.Enable(True)
        missing_count = len(self._rows_missing)
        all_count = len(self._rows_all)
        resolved_count = sum(1 for r in self._rows_all if r.is_resolved)
        field_count = len(self._rows_field)
        if missing_count == 0 and field_count == 0:
            self._set_status(
                f"All required datasheets resolved ({resolved_count}/{all_count} parts).",
                "Symbol Datasheet fields look OK.",
            )
        elif missing_count == 0:
            self._set_status(
                f"All required PDFs resolved ({resolved_count}/{all_count} parts).",
                f"{field_count} part(s) need symbol Datasheet field cleanup — see Symbol field tab.",
            )
        else:
            self._set_status(
                f"{missing_count} part(s) need PDFs — "
                f"{resolved_count}/{all_count} required parts resolved.",
                (
                    f"{field_count} symbol field issue(s) — Symbol field tab."
                    if field_count
                    else "Select a row for full detail (right-click to copy)."
                ),
            )
        self._layout_panel()

    def _pdf_source_text(self, row: MissingDatasheetRow) -> str:
        if row.local_path:
            return Path(row.local_path).name
        if row.artifact_id:
            return row.artifact_id
        return ""

    def _field_symbol_text(self, row: MissingDatasheetRow) -> str:
        if row.symbol_fields:
            return row.symbol_fields[0][:80]
        return (row.symbol_datasheet_url or "")[:80]

    def _populate_list(
        self,
        lst: wx.ListCtrl,
        rows: list[MissingDatasheetRow],
        *,
        include_pdf_column: bool = False,
        include_field_columns: bool = False,
    ) -> None:
        lst.DeleteAllItems()
        for i, row in enumerate(rows):
            lst.InsertItem(i, row.part)
            lst.SetItem(i, 1, str(row.reference_count))
            if include_field_columns:
                status = self._row_status.get(row.part) or row.field_issue_label or row.status
                lst.SetItem(i, 2, status)
                lst.SetItem(i, 3, self._field_symbol_text(row))
                lst.SetItem(i, 4, (row.resolved_url or "")[:80])
                lst.SetItem(i, 5, (row.field_issue_detail or self._detail_text(row))[:200])
            else:
                status = self._row_status.get(row.part) or row.discovery_status or row.status
                lst.SetItem(i, 2, status)
                if include_pdf_column:
                    lst.SetItem(i, 3, self._pdf_source_text(row)[:80])
                    lst.SetItem(i, 4, self._detail_text(row))
                else:
                    lst.SetItem(i, 3, self._detail_text(row))
            lst.SetItemData(i, i)

    def _refresh_rows(self, *, preserve_status: bool = False) -> None:
        saved_status = dict(self._row_status) if preserve_status else {}
        ctx, self._rows_missing = get_missing_datasheet_rows(
            self._project_path,
            config=self._cfg,
            retry_failed_urls=self._retry_failed_urls,
            force_refresh_urls=self._force_refresh_urls,
            datasheet_ai_discovery=False,
            verbose=False,
        )
        self._rows_all = build_required_rows_from_context(ctx, config=self._cfg)
        self._rows_field = build_field_issue_rows_from_context(ctx, config=self._cfg)
        self._populate_list(self._list_missing, self._rows_missing, include_pdf_column=False)
        self._populate_list(self._list_all, self._rows_all, include_pdf_column=True)
        self._populate_list(
            self._list_field,
            self._rows_field,
            include_field_columns=True,
        )

        if preserve_status:
            self._row_status.update(saved_status)
            self._repaint_list_status()

        if not self._rows_missing:
            self._btn_attach.Enable(False)
            self._btn_ai.Enable(False)
        else:
            self._btn_attach.Enable(True)
            self._update_ai_button_state()

        missing_count = len(self._rows_missing)
        all_count = len(self._rows_all)
        resolved_count = sum(1 for r in self._rows_all if r.is_resolved)
        if not preserve_status:
            field_count = len(self._rows_field)
            if missing_count == 0 and field_count == 0:
                self._set_status(
                    f"All required datasheets resolved ({resolved_count}/{all_count} parts).",
                    "Symbol Datasheet fields look OK.",
                )
            elif missing_count == 0:
                self._set_status(
                    f"All required PDFs resolved ({resolved_count}/{all_count} parts).",
                    f"{field_count} part(s) need symbol Datasheet field cleanup — see Symbol field tab.",
                )
            else:
                self._set_status(
                    f"{missing_count} part(s) need PDFs — "
                    f"{resolved_count}/{all_count} required parts resolved.",
                    (
                        f"{field_count} symbol field issue(s) — Symbol field tab."
                        if field_count
                        else "Select a row, then Attach, Reset, or Find with AI."
                    ),
                )
        self._layout_panel()


