"""Unified Assistant shell (ADP-011) — embedded tabbed panel with shared project header."""

from __future__ import annotations

from pathlib import Path

from ui.aerf_dialog import show_aerf_dialog
from ui.assistant_tab import ASSISTANT_TAB_IDS, AssistantTabPanel, tab_index_for_focus
from ui.chat_dialog import show_chat_dialog
from ui.context_controller import ContextController
from ui.launcher import (
    effective_initial_project_path,
    present_top_level_window,
    resolve_project_pro_path,
    run_wx_main_loop_if_needed,
)
from ui.kicad_host import prepare_kicad_ui_launch
from ui.launcher_dialog import normalize_launcher_project_path
from ui.missing_datasheets_dialog import show_missing_datasheets_dialog
from ui.notebook_tab import NotebookTab
from ui.placeholder_tab import PlaceholderTab
from ui.simulation_dialog import show_simulation_dialog
from utils.config import load_config

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class AssistantShell(wx.Panel):
    """Shared header, context controller, and feature tabs."""

    def __init__(
        self,
        parent: wx.Window,
        initial_path: Path | str | None = None,
        *,
        focus_tab: str | None = None,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for AssistantShell")
        super().__init__(parent)
        self._controller = ContextController(config=load_config())
        self._controller.bind_listener(self._on_context_refreshed)
        self._tabs: dict[str, AssistantTabPanel] = {}
        self._placeholder_tabs: dict[str, PlaceholderTab] = {}
        self._notebook_tab: NotebookTab | None = None

        vbox = wx.BoxSizer(wx.VERTICAL)

        intro = wx.StaticText(
            self,
            label=(
                "Unified Assistant shell — shared project context and feature tabs. "
                "Notebook is embedded; other tabs open legacy panels until Sprint 2."
            ),
        )
        intro.Wrap(760)
        vbox.Add(intro, flag=wx.ALL, border=8)

        path_row = wx.BoxSizer(wx.HORIZONTAL)
        path_row.Add(wx.StaticText(self, label="Project:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=6)
        self._txt_path = wx.TextCtrl(self)
        effective_path = effective_initial_project_path(initial_path)
        if effective_path is not None:
            try:
                self._txt_path.SetValue(str(resolve_project_pro_path(effective_path)))
            except (FileNotFoundError, OSError):
                self._txt_path.SetValue(str(effective_path))
        path_row.Add(self._txt_path, proportion=1, flag=wx.RIGHT, border=6)
        self._btn_browse = wx.Button(self, label="Browse…")
        self._btn_refresh = wx.Button(self, label="Refresh context")
        path_row.Add(self._btn_browse, flag=wx.RIGHT, border=4)
        path_row.Add(self._btn_refresh)
        vbox.Add(path_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        self._summary = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self._summary.SetMinSize((-1, 140))
        vbox.Add(self._summary, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        self._notebook = wx.Notebook(self)
        modal_parent = self.GetTopLevelParent()

        placeholder_specs: tuple[tuple[str, str, str, object], ...] = (
            (
                "chat",
                "Chat",
                "Ad-hoc Q&A (general_review). Not full AERF.",
                lambda pro, parent: show_chat_dialog(pro, parent=parent),
            ),
            (
                "datasheets",
                "Datasheets",
                "Attach PDFs and resolve missing datasheets.",
                lambda pro, parent: show_missing_datasheets_dialog(pro, parent=parent),
            ),
            (
                "simulation",
                "Simulation",
                "SPICE gap scan and SUBCKT generation.",
                lambda pro, parent: show_simulation_dialog(pro, parent=parent),
            ),
            (
                "aerf",
                "AERF",
                "Staged engineer analysis (stages 0–7).",
                lambda pro, parent: show_aerf_dialog(pro, parent=parent),
            ),
        )
        for tab_id, label, hint, opener in placeholder_specs:
            tab = PlaceholderTab(
                self._notebook,
                tab_id=tab_id,
                label=label,
                hint=hint,
                open_modal=opener,
                modal_parent=modal_parent,
            )
            self._notebook.AddPage(tab, label)
            self._tabs[tab_id] = tab
            self._placeholder_tabs[tab_id] = tab

        notebook_tab = NotebookTab(self._notebook)
        self._notebook.AddPage(notebook_tab, "Notebook")
        self._tabs["notebook"] = notebook_tab
        self._notebook_tab = notebook_tab

        vbox.Add(self._notebook, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)

        self._status = wx.StaticText(self, label="Select a project and refresh context.")
        vbox.Add(self._status, flag=wx.ALL, border=8)

        self.SetSizer(vbox)

        self._btn_browse.Bind(wx.EVT_BUTTON, self._on_browse)
        self._btn_refresh.Bind(wx.EVT_BUTTON, self._on_refresh)
        self._notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._on_tab_changed)

        focus_idx = tab_index_for_focus(focus_tab)
        if focus_idx is not None:
            self._notebook.SetSelection(focus_idx)

        if effective_path is not None:
            self._on_refresh(None)

        self._notify_active_tab_selected()

    def confirm_close(self) -> bool:
        """Return False when the embedded notebook has unsaved edits."""
        if self._notebook_tab is not None and not self._notebook_tab.confirm_discard():
            return False
        return True

    def open_placeholder_panel(self, tab_id: str) -> None:
        """Select a placeholder tab and open its legacy modal panel."""
        if tab_id not in self._placeholder_tabs:
            return
        idx = ASSISTANT_TAB_IDS.index(tab_id)
        self._notebook.SetSelection(idx)
        self._placeholder_tabs[tab_id].open_modal_panel()

    def _on_browse(self, _event: wx.CommandEvent) -> None:
        dlg = wx.FileDialog(
            self,
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
        self.Layout()
        self._controller.refresh(pro)
        if self._controller.last_error:
            self._status.SetLabel(f"Context error: {self._controller.last_error}")
            return
        self._summary.SetValue(self._controller.summary_text)
        self._status.SetLabel(f"Context ready — {pro.name}")

    def _on_context_refreshed(self, ctx, summary: str) -> None:
        for tab in self._tabs.values():
            tab.on_context_refreshed(ctx, summary)

    def _on_tab_changed(self, _event: wx.NotebookEvent) -> None:
        self._notify_active_tab_selected()

    def _notify_active_tab_selected(self) -> None:
        idx = self._notebook.GetSelection()
        if idx < 0:
            return
        page = self._notebook.GetPage(idx)
        if isinstance(page, AssistantTabPanel):
            page.on_tab_selected()

    def _active_tab_panel(self) -> AssistantTabPanel | None:
        idx = self._notebook.GetSelection()
        if idx < 0:
            return None
        page = self._notebook.GetPage(idx)
        if isinstance(page, AssistantTabPanel):
            return page
        return None


def show_assistant_shell(
    project_path: Path | str | None = None,
    *,
    parent: wx.Window | None = None,
    focus_tab: str | None = None,
    open_focus_panel: bool = False,
) -> None:
    """Show the unified Assistant shell in a standalone frame."""
    if wx is None:
        raise RuntimeError("wxPython is required; run inside KiCad or install wx on PYTHONPATH")
    from ui.kicad_host import prepare_kicad_ui_launch

    ok, kicad_parent = prepare_kicad_ui_launch(parent)
    if not ok:
        return
    from ui.assistant_frame import AssistantFrame

    frame = AssistantFrame(kicad_parent, initial_path=project_path, focus_tab=focus_tab)
    present_top_level_window(frame, kicad_parent)
    if open_focus_panel and focus_tab and focus_tab != "notebook":
        frame.open_placeholder_panel(focus_tab)
    run_wx_main_loop_if_needed()
