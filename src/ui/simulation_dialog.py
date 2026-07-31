"""Simulation / SUBCKT gap-fill panel (wxPython)."""

from __future__ import annotations

from pathlib import Path

from ui.simulation_supply import (
    GAP_LABELS,
    SimulationPanelContext,
    apply_simulation_model_for_part,
    apply_spice_fields_for_part,
    get_simulation_panel_context,
    run_subckt_generation,
)
from context.schematic_write import format_spice_write_success_message
from context.subckt_generation import SubcktGenerationResult
from utils.config import load_config

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class SimulationDialog(wx.Dialog if wx else object):  # type: ignore[misc]
    """List simulation model gaps and generate SUBCKT .lib files."""

    def __init__(
        self,
        parent: object | None,
        project_path: Path,
        *,
        config=None,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for the Simulation panel")
        self._cfg = config or load_config()
        self._project_path = project_path.expanduser().resolve()
        super().__init__(
            parent,
            title="Simulation models (SUBCKT)",
            size=(860, 560),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._busy = False
        self._panel_ctx: SimulationPanelContext | None = None
        self._last_result: SubcktGenerationResult | None = None
        self._build_ui()
        self._refresh_rows()

    def _build_ui(self) -> None:
        outer = wx.BoxSizer(wx.VERTICAL)
        intro = wx.StaticText(
            self,
            label=(
                "Detect missing ngspice SUBCKT models and KiCad 9 simulation hookup gaps. "
                "Built-in models for R/C/L/diodes are applied automatically on Refresh context. "
                "Parts already hooked up (Sim.Device=SUBCKT) appear on the All required tab only."
            ),
        )
        intro.Wrap(820)
        outer.Add(intro, flag=wx.ALL | wx.EXPAND, border=10)

        self._notebook = wx.Notebook(self)
        self._list_missing = self._make_list(self._notebook)
        self._list_all = self._make_list(self._notebook)
        self._notebook.AddPage(self._list_missing, "Missing models")
        self._notebook.AddPage(self._list_all, "All required")
        outer.Add(self._notebook, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        self._footer = wx.Panel(self)
        footer_sizer = wx.BoxSizer(wx.VERTICAL)
        self._status = wx.TextCtrl(
            self._footer,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 52),
        )
        footer_sizer.Add(self._status, flag=wx.EXPAND | wx.BOTTOM, border=6)
        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_generate = wx.Button(self._footer, label="Generate SUBCKT…")
        self._btn_apply_spice = wx.Button(self._footer, label="Apply simulation model…")
        self._btn_refresh = wx.Button(self._footer, label="Refresh")
        self._btn_close = wx.Button(self._footer, wx.ID_CLOSE, label="Close")
        btn_row.Add(self._btn_generate, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_apply_spice, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_refresh, flag=wx.RIGHT, border=6)
        btn_row.AddStretchSpacer()
        btn_row.Add(self._btn_close)
        footer_sizer.Add(btn_row, flag=wx.EXPAND)
        self._footer.SetSizer(footer_sizer)
        outer.Add(self._footer, flag=wx.EXPAND | wx.ALL, border=10)
        self.SetSizer(outer)

        self._btn_generate.Bind(wx.EVT_BUTTON, self._on_generate)
        self._btn_apply_spice.Bind(wx.EVT_BUTTON, self._on_apply_spice)
        self._btn_refresh.Bind(wx.EVT_BUTTON, lambda _e: self._refresh_rows())
        self._btn_close.Bind(wx.EVT_BUTTON, lambda _e: self.Close())

    def _make_list(self, parent: wx.Window) -> wx.ListCtrl:
        lst = wx.ListCtrl(parent, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        lst.InsertColumn(0, "Part (Value)", width=140)
        lst.InsertColumn(1, "Refs", width=70)
        lst.InsertColumn(2, "Gap", width=180)
        lst.InsertColumn(3, "Tier", width=50)
        lst.InsertColumn(4, "PDF", width=50)
        lst.InsertColumn(5, "Spice_Model", width=120)
        lst.InsertColumn(6, "Sim.Device", width=90)
        return lst

    def _active_list(self) -> wx.ListCtrl:
        return self._list_missing if self._notebook.GetSelection() == 0 else self._list_all

    def _selected_row(self):
        if self._panel_ctx is None:
            return None
        tab = self._notebook.GetSelection()
        rows = self._panel_ctx.rows_missing if tab == 0 else self._panel_ctx.rows_all
        idx = self._active_list().GetFirstSelected()
        if idx < 0 or idx >= len(rows):
            return None
        return rows[idx]

    def _populate(self, lst: wx.ListCtrl, rows) -> None:
        lst.DeleteAllItems()
        for i, row in enumerate(rows):
            lst.InsertItem(i, row.part)
            lst.SetItem(i, 1, str(row.reference_count))
            lst.SetItem(i, 2, GAP_LABELS.get(row.gap_kind, row.gap_kind))
            lst.SetItem(i, 3, row.tier_hint)
            lst.SetItem(i, 4, "yes" if row.datasheet_resolved else "no")
            lst.SetItem(i, 5, row.spice_model or "(empty)")
            sim_dev = getattr(row, "sim_device", "") or ""
            lst.SetItem(i, 6, sim_dev or "(none)")

    def _set_status(self, line1: str, line2: str = "") -> None:
        text = line1 if not line2 else f"{line1}\n{line2}"
        self._status.SetValue(text[:500])

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        for btn in (self._btn_generate, self._btn_apply_spice, self._btn_refresh):
            btn.Enable(not busy)

    def _refresh_rows(self) -> None:
        try:
            self._panel_ctx = get_simulation_panel_context(
                self._project_path,
                config=self._cfg,
                verbose=False,
            )
        except Exception as exc:
            self._set_status("Failed to load simulation gaps.", str(exc))
            return
        self._populate(self._list_missing, self._panel_ctx.rows_missing)
        self._populate(self._list_all, self._panel_ctx.rows_all)
        n = len(self._panel_ctx.rows_missing)
        self._set_status(
            f"{n} part(s) missing simulation models.",
            f"Project: {self._panel_ctx.ctx.project_name}",
        )

    def _on_generate(self, _event: wx.CommandEvent) -> None:
        if self._busy:
            return
        row = self._selected_row()
        if row is None:
            wx.MessageBox(
                "Select a part row first.",
                "Generate SUBCKT",
                wx.OK | wx.ICON_INFORMATION,
            )
            return
        if not self._cfg.anthropic_api_key:
            wx.MessageBox(
                "Anthropic API key required for SUBCKT generation.\n"
                "Set ANTHROPIC_API_KEY or anthropic_api_key in ~/kicad_ai_config.json.",
                "Generate SUBCKT",
                wx.OK | wx.ICON_WARNING,
            )
            return
        tier = row.tier_hint
        msg = (
            f"Generate draft ngspice .lib for {row.part}?\n\n"
            f"Strategy tier: {tier}\n"
            f"Datasheet PDF: {'resolved' if row.datasheet_resolved else 'not available'}\n\n"
            "Output is advisory — verify before simulation."
        )
        if wx.MessageBox(msg, "Generate SUBCKT", wx.OK | wx.CANCEL | wx.ICON_QUESTION) != wx.OK:
            return
        self._set_busy(True)
        self._set_status(f"Generating SUBCKT for {row.part} (Tier {tier})…")

        def work() -> None:
            try:
                panel, result = run_subckt_generation(
                    self._project_path,
                    row.part,
                    config=self._cfg,
                    tier=tier,
                )
                wx.CallAfter(self._on_generate_done, panel, result)
            except Exception as exc:
                wx.CallAfter(self._on_generate_done, None, None, str(exc))

        import threading

        threading.Thread(target=work, daemon=True).start()

    def _on_generate_done(
        self,
        panel: SimulationPanelContext | None,
        result: SubcktGenerationResult | None,
        error: str | None = None,
    ) -> None:
        self._set_busy(False)
        if error:
            self._set_status("SUBCKT generation failed.", error)
            wx.MessageBox(error, "Generate SUBCKT", wx.OK | wx.ICON_ERROR)
            return
        if result is None or panel is None:
            return
        self._panel_ctx = panel
        self._last_result = result
        self._populate(self._list_missing, panel.rows_missing)
        self._populate(self._list_all, panel.rows_all)
        if result.error:
            self._set_status(f"SUBCKT failed for {result.part}.", result.error)
            wx.MessageBox(result.error, "Generate SUBCKT", wx.OK | wx.ICON_WARNING)
            return
        lib = str(result.lib_path) if result.lib_path else "(unknown)"
        self._set_status(
            f"Generated {result.part}.lib ({result.tier_label}).",
            f"Validation: {result.validation_status} — {lib}",
        )
        notes = result.hookup.markdown if result.hookup else ""
        wx.MessageBox(
            f"SUBCKT registered for {result.part}.\n\n"
            f"Tier: {result.tier_label}\n"
            f"Validation: {result.validation_status}\n"
            f"Library: {lib}\n\n"
            f"{notes[:1200]}",
            "Generate SUBCKT",
            wx.OK | wx.ICON_INFORMATION,
        )

    def _on_apply_spice(self, _event: wx.CommandEvent) -> None:
        if self._busy:
            return
        row = self._selected_row()
        if row is None:
            wx.MessageBox(
                "Select a part row first.",
                "Apply simulation model",
                wx.OK | wx.ICON_INFORMATION,
            )
            return
        hookup = self._last_result.hookup if (
            self._last_result and self._last_result.part == row.part
        ) else None
        if hookup is not None:
            panel, result = apply_spice_fields_for_part(
                self._project_path,
                row.part,
                spice_model=hookup.spice_model,
                spice_lib=hookup.spice_lib,
                spice_primitive=hookup.spice_primitive,
                config=self._cfg,
            )
        else:
            panel, result = apply_simulation_model_for_part(
                self._project_path,
                row.part,
                config=self._cfg,
            )
        if result is None or result.changed_count == 0:
            detail = (
                result.skipped[0]
                if result and result.skipped
                else "No .lib found in catalog or symbol Spice_Lib field."
            )
            wx.MessageBox(detail, "Apply simulation model", wx.OK | wx.ICON_INFORMATION)
            return
        wx.MessageBox(
            format_spice_write_success_message(result),
            "Apply simulation model",
            wx.OK | wx.ICON_INFORMATION,
        )
        refreshed = get_simulation_panel_context(self._project_path, config=self._cfg)
        self._panel_ctx = refreshed
        self._populate(self._list_missing, refreshed.rows_missing)
        self._populate(self._list_all, refreshed.rows_all)
        self._set_status(
            f"Applied KiCad 9 simulation model for {row.part}.",
            "File → Revert in KiCad to refresh Symbol Properties.",
        )


def show_simulation_dialog(
    project_path: Path | str,
    *,
    config=None,
    parent: object | None = None,
) -> None:
    """Open the Simulation models panel (modal)."""
    if wx is None:
        raise RuntimeError("wxPython is required")
    path = Path(project_path).expanduser().resolve()
    dlg = SimulationDialog(parent, path, config=config)
    dlg.ShowModal()
    dlg.Destroy()
