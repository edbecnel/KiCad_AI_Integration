"""Unified Assistant shell (ADP-011 scaffold) — tabbed frame with shared project header."""

from __future__ import annotations

from pathlib import Path

from ui.aerf_dialog import show_aerf_dialog
from ui.chat_dialog import show_chat_dialog
from ui.launcher import ensure_wx_app, resolve_project_pro_path
from ui.launcher_dialog import build_launcher_context_summary, normalize_launcher_project_path
from ui.missing_datasheets_dialog import show_missing_datasheets_dialog
from ui.notebook_dialog import show_notebook_dialog
from ui.simulation_dialog import show_simulation_dialog

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class AssistantShellFrame:
    """Non-modal shell with shared project path and feature tabs."""

    def __init__(
        self,
        parent: wx.Window | None,
        initial_path: Path | str | None = None,
        *,
        focus_tab: str | None = None,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for AssistantShellFrame")
        self._frame = wx.Frame(
            parent,
            title="KiCad AI Assistant",
            size=(820, 680),
            style=wx.DEFAULT_FRAME_STYLE,
        )
        panel = wx.Panel(self._frame)
        vbox = wx.BoxSizer(wx.VERTICAL)

        intro = wx.StaticText(
            panel,
            label=(
                "Unified Assistant shell — shared project context and feature tabs. "
                "Each tab opens the feature panel as a child window."
            ),
        )
        intro.Wrap(760)
        vbox.Add(intro, flag=wx.ALL, border=8)

        path_row = wx.BoxSizer(wx.HORIZONTAL)
        path_row.Add(wx.StaticText(panel, label="Project:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=6)
        self._txt_path = wx.TextCtrl(panel)
        if initial_path:
            try:
                self._txt_path.SetValue(str(resolve_project_pro_path(initial_path)))
            except (FileNotFoundError, OSError):
                self._txt_path.SetValue(str(initial_path))
        path_row.Add(self._txt_path, proportion=1, flag=wx.RIGHT, border=6)
        self._btn_browse = wx.Button(panel, label="Browse…")
        self._btn_refresh = wx.Button(panel, label="Refresh context")
        path_row.Add(self._btn_browse, flag=wx.RIGHT, border=4)
        path_row.Add(self._btn_refresh)
        vbox.Add(path_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        self._summary = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self._summary.SetMinSize((-1, 140))
        vbox.Add(self._summary, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        self._notebook = wx.Notebook(panel)
        self._tabs: dict[str, wx.Panel] = {}
        for tab_id, label, hint in (
            ("chat", "Chat", "Ad-hoc Q&A (general_review). Not full AERF."),
            ("datasheets", "Datasheets", "Attach PDFs and resolve missing datasheets."),
            ("simulation", "Simulation", "SPICE gap scan and SUBCKT generation."),
            ("aerf", "AERF", "Staged engineer analysis (stages 0–7)."),
            ("notebook", "Notebook", "Engineering Knowledge Model editor."),
        ):
            tab_panel = wx.Panel(self._notebook)
            tab_vbox = wx.BoxSizer(wx.VERTICAL)
            hint_ctrl = wx.StaticText(tab_panel, label=hint)
            hint_ctrl.Wrap(700)
            tab_vbox.Add(hint_ctrl, flag=wx.ALL, border=10)
            open_btn = wx.Button(tab_panel, label=f"Open {label} panel")
            open_btn.Bind(wx.EVT_BUTTON, lambda _e, t=tab_id: self._open_panel(t))
            tab_vbox.Add(open_btn, flag=wx.LEFT | wx.BOTTOM, border=10)
            tab_panel.SetSizer(tab_vbox)
            self._notebook.AddPage(tab_panel, label)
            self._tabs[tab_id] = tab_panel

        vbox.Add(self._notebook, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)

        self._status = wx.StaticText(panel, label="Select a project and refresh context.")
        vbox.Add(self._status, flag=wx.ALL, border=8)

        panel.SetSizer(vbox)

        self._btn_browse.Bind(wx.EVT_BUTTON, self._on_browse)
        self._btn_refresh.Bind(wx.EVT_BUTTON, self._on_refresh)

        if initial_path:
            self._on_refresh(None)

        if focus_tab and focus_tab in self._tabs:
            idx = list(self._tabs.keys()).index(focus_tab)
            self._notebook.SetSelection(idx)

    def show(self) -> None:
        self._frame.Show()

    def _on_browse(self, _event: wx.CommandEvent) -> None:
        dlg = wx.FileDialog(
            self._frame,
            "Select KiCad project",
            wildcard="KiCad project (*.kicad_pro)|*.kicad_pro",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self._txt_path.SetValue(dlg.GetPath())
        dlg.Destroy()

    def _on_refresh(self, _event: wx.CommandEvent | None) -> None:
        try:
            pro = normalize_launcher_project_path(self._txt_path.GetValue())
        except (ValueError, FileNotFoundError, OSError) as exc:
            self._status.SetLabel(str(exc))
            return
        self._status.SetLabel("Collecting context…")
        self._frame.Layout()
        try:
            summary = build_launcher_context_summary(pro)
        except OSError as exc:
            self._status.SetLabel(f"Context error: {exc}")
            return
        self._summary.SetValue(summary)
        self._status.SetLabel(f"Context ready — {pro.name}")

    def _project_path(self) -> Path:
        return normalize_launcher_project_path(self._txt_path.GetValue())

    def _open_panel(self, panel: str) -> None:
        try:
            pro = self._project_path()
        except (ValueError, FileNotFoundError, OSError) as exc:
            wx.MessageBox(str(exc), "KiCad AI Assistant", wx.OK | wx.ICON_WARNING)
            return
        parent = self._frame
        if panel == "chat":
            show_chat_dialog(pro, parent=parent)
        elif panel == "datasheets":
            show_missing_datasheets_dialog(pro, parent=parent)
        elif panel == "simulation":
            show_simulation_dialog(pro, parent=parent)
        elif panel == "aerf":
            show_aerf_dialog(pro, parent=parent)
        elif panel == "notebook":
            show_notebook_dialog(pro, parent=parent)


def show_assistant_shell(
    project_path: Path | str | None = None,
    *,
    parent: wx.Window | None = None,
    focus_tab: str | None = None,
    open_focus_panel: bool = False,
) -> None:
    """Show the unified Assistant shell (non-modal frame)."""
    if wx is None:
        raise RuntimeError("wxPython is required; run inside KiCad or install wx on PYTHONPATH")
    ensure_wx_app()
    shell = AssistantShellFrame(parent, initial_path=project_path, focus_tab=focus_tab)
    shell.show()
    if open_focus_panel and focus_tab:
        shell._open_panel(focus_tab)
