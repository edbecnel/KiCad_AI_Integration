"""Missing required datasheets panel (wxPython)."""

from __future__ import annotations

from pathlib import Path

from ui.datasheet_supply import (
    MissingDatasheetRow,
    attach_datasheet_pdf,
    get_missing_datasheet_rows,
    manual_pdf_path_for_part,
)
from utils.config import load_config

try:
    import wx
except ImportError:  # pragma: no cover - wx only inside KiCad
    wx = None  # type: ignore[assignment]


class MissingDatasheetsDialog:
    """Modal dialog listing datasheet-required parts still missing a PDF."""

    def __init__(
        self,
        parent: wx.Window | None,
        project_path: Path,
        *,
        retry_failed_urls: bool = False,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for MissingDatasheetsDialog")
        self._project_path = project_path.expanduser().resolve()
        self._retry_failed_urls = retry_failed_urls
        self._cfg = load_config()
        self._rows: list[MissingDatasheetRow] = []

        self._dialog = wx.Dialog(
            parent,
            title="Missing Required Datasheets",
            size=(720, 420),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        panel = wx.Panel(self._dialog)
        vbox = wx.BoxSizer(wx.VERTICAL)

        intro = wx.StaticText(
            panel,
            label=(
                "These parts need a datasheet PDF for detailed / SUBCKT analysis. "
                "Use Attach PDF to register a file for the part Value, or save manually as "
                f"{manual_pdf_path_for_part(self._cfg.artifact_library_path, '<Value>')}."
            ),
        )
        intro.Wrap(680)
        vbox.Add(intro, flag=wx.ALL | wx.EXPAND, border=10)

        self._list = wx.ListCtrl(
            panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN,
        )
        self._list.InsertColumn(0, "Part (Value)", width=140)
        self._list.InsertColumn(1, "Refs", width=50)
        self._list.InsertColumn(2, "Status", width=90)
        self._list.InsertColumn(3, "Error / URL", width=380)
        vbox.Add(self._list, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_attach = wx.Button(panel, label="Attach PDF…")
        self._btn_refresh = wx.Button(panel, label="Refresh")
        self._btn_close = wx.Button(panel, label="Close")
        btn_row.Add(self._btn_attach, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_refresh, flag=wx.RIGHT, border=6)
        btn_row.AddStretchSpacer()
        btn_row.Add(self._btn_close)
        vbox.Add(btn_row, flag=wx.EXPAND | wx.ALL, border=10)

        self._status = wx.StaticText(panel, label="")
        vbox.Add(self._status, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        panel.SetSizer(vbox)

        self._btn_attach.Bind(wx.EVT_BUTTON, self._on_attach)
        self._btn_refresh.Bind(wx.EVT_BUTTON, self._on_refresh)
        self._btn_close.Bind(wx.EVT_BUTTON, self._on_close)

        self._refresh_rows()

    def show_modal(self) -> int:
        return self._dialog.ShowModal()

    def _on_close(self, _event: wx.CommandEvent) -> None:
        self._dialog.EndModal(wx.ID_OK)

    def _on_refresh(self, _event: wx.CommandEvent) -> None:
        self._refresh_rows()

    def _selected_row(self) -> MissingDatasheetRow | None:
        idx = self._list.GetFirstSelected()
        if idx == -1 or idx >= len(self._rows):
            return None
        return self._rows[idx]

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
            self._dialog,
            f"Attach datasheet PDF for {row.part}",
            wildcard="PDF files (*.pdf)|*.pdf",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            pdf_path = Path(dlg.GetPath())
        try:
            attach_datasheet_pdf(
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
        self._status.SetLabel(f"Attached {pdf_path.name} for {row.part}.")
        self._refresh_rows()

    def _refresh_rows(self) -> None:
        self._list.DeleteAllItems()
        _, self._rows = get_missing_datasheet_rows(
            self._project_path,
            config=self._cfg,
            retry_failed_urls=self._retry_failed_urls,
            verbose=False,
        )
        if not self._rows:
            self._list.InsertItem(0, "(none)")
            self._list.SetItem(0, 1, "")
            self._list.SetItem(0, 2, "resolved")
            self._list.SetItem(0, 3, "All required datasheets are resolved.")
            self._btn_attach.Enable(False)
            self._status.SetLabel("")
            return
        self._btn_attach.Enable(True)
        for i, row in enumerate(self._rows):
            self._list.InsertItem(i, row.part)
            self._list.SetItem(i, 1, str(row.reference_count))
            self._list.SetItem(i, 2, row.status)
            detail = row.errors[0] if row.errors else ""
            if row.symbol_datasheet_url:
                detail = f"{detail} | {row.symbol_datasheet_url}".strip(" |")
            self._list.SetItem(i, 3, detail[:200])
            self._list.SetItemData(i, i)
        self._status.SetLabel(
            f"{len(self._rows)} part(s) need PDFs — "
            f"manual path example: {manual_pdf_path_for_part(self._cfg.artifact_library_path, self._rows[0].part)}"
        )


def show_missing_datasheets_dialog(
    project_path: Path | str,
    *,
    parent: wx.Window | None = None,
    retry_failed_urls: bool = False,
) -> None:
    """Show the missing datasheets dialog modally."""
    if wx is None:
        raise RuntimeError("wxPython is required; run inside KiCad or install wx on PYTHONPATH")
    path = Path(project_path).expanduser()
    dlg = MissingDatasheetsDialog(parent, path, retry_failed_urls=retry_failed_urls)
    dlg.show_modal()
