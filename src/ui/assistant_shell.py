"""Unified Assistant shell (ADP-011) — embedded tabbed panel with shared project header."""

from __future__ import annotations

from pathlib import Path

from context.datasheet_requirements import summarize_required_missing_datasheets
from ui.aerf_tab import AERFTab
from ui.audits_tab import AuditsTab
from ui.routing_tab import RoutingTab
from ui.assistant_tab import ASSISTANT_TAB_IDS, AssistantTabPanel, tab_index_for_focus
from ui.chat_tab import ChatTab
from ui.context_controller import ContextController
from ui.datasheets_tab import DatasheetsTab
from ui.launcher import (
    effective_initial_project_path,
    resolve_project_pro_path,
    run_wx_main_loop_if_needed,
)
from ui.kicad_host import prepare_kicad_ui_launch
from ui.project_path import normalize_launcher_project_path
from ui.notebook_tab import NotebookTab
from ui.simulation_tab import SimulationTab
from ui.shell_preferences import get_last_tab, set_last_tab
from ui.settings_dialog import show_settings_dialog
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
        self._notebook_tab: NotebookTab | None = None
        self._tab_labels: dict[str, str] = {
            "chat": "Chat",
            "datasheets": "Datasheets",
            "simulation": "Simulation",
            "aerf": "AERF",
            "notebook": "Notebook",
            "audits": "Audits",
            "routing": "Routing",
        }

        vbox = wx.BoxSizer(wx.VERTICAL)

        intro = wx.StaticText(
            self,
            label=(
                "Unified Assistant shell — shared project context and embedded feature tabs. "
                "Refresh context once in the header; each tab updates from the same project."
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
        path_row.Add(self._txt_path, proportion=1, flag=wx.EXPAND)
        vbox.Add(path_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=8)

        header_btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_browse = wx.Button(self, label="Browse…")
        self._btn_refresh = wx.Button(self, label="Refresh context")
        self._btn_settings = wx.Button(self, label="Settings…")
        header_btn_row.Add(self._btn_browse, flag=wx.RIGHT, border=4)
        header_btn_row.Add(self._btn_refresh, flag=wx.RIGHT, border=4)
        header_btn_row.Add(self._btn_settings)
        header_btn_row.AddStretchSpacer()
        vbox.Add(header_btn_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        self._summary = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self._summary.SetMinSize((-1, 80))
        vbox.Add(self._summary, proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        self._notebook = wx.Notebook(self)

        tab_specs: tuple[tuple[str, str, type[AssistantTabPanel]], ...] = (
            ("chat", "Chat", ChatTab),
            ("datasheets", "Datasheets", DatasheetsTab),
            ("simulation", "Simulation", SimulationTab),
            ("aerf", "AERF", AERFTab),
        )
        for tab_id, label, tab_cls in tab_specs:
            tab = tab_cls(self._notebook)
            self._notebook.AddPage(tab, label)
            self._tabs[tab_id] = tab
            self._tab_labels[tab_id] = label

        notebook_tab = NotebookTab(self._notebook)
        self._notebook.AddPage(notebook_tab, "Notebook")
        self._tabs["notebook"] = notebook_tab
        self._notebook_tab = notebook_tab

        audits_tab = AuditsTab(self._notebook)
        self._notebook.AddPage(audits_tab, "Audits")
        self._tabs["audits"] = audits_tab

        routing_tab = RoutingTab(self._notebook)
        self._notebook.AddPage(routing_tab, "Routing")
        self._tabs["routing"] = routing_tab

        vbox.Add(self._notebook, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)

        self._status = wx.StaticText(self, label="Select a project and refresh context.")
        vbox.Add(self._status, flag=wx.ALL, border=8)

        self.SetSizer(vbox)

        self._btn_browse.Bind(wx.EVT_BUTTON, self._on_browse)
        self._btn_refresh.Bind(wx.EVT_BUTTON, self._on_refresh)
        self._btn_settings.Bind(wx.EVT_BUTTON, self._on_settings)
        self._notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._on_tab_changed)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)

        focus_idx = tab_index_for_focus(focus_tab)
        if focus_idx is None and effective_path is not None:
            saved_tab = get_last_tab(effective_path)
            focus_idx = tab_index_for_focus(saved_tab)
        if focus_idx is not None:
            self._notebook.SetSelection(focus_idx)

        if effective_path is not None:
            self._on_refresh(None)

        self._notify_active_tab_selected()

    def confirm_close(self) -> bool:
        """Return False when any tab blocks close (unsaved edits or busy operations)."""
        for tab in self._tabs.values():
            if not tab.confirm_discard():
                return False
        return True

    def focus_tab(self, tab_id: str) -> None:
        """Select a tab by id (CLI deep links)."""
        if tab_id not in ASSISTANT_TAB_IDS:
            return
        self._notebook.SetSelection(ASSISTANT_TAB_IDS.index(tab_id))
        self._notify_active_tab_selected()

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

    def _on_settings(self, _event: wx.CommandEvent) -> None:
        saved = show_settings_dialog(self, config=self._controller._config or load_config())
        if saved is not None:
            self._controller._config = saved
            self._status.SetLabel(f"Settings saved — provider: {saved.ai_provider}")

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
        self._update_tab_badges(self._controller.context)

    def _update_tab_badges(self, ctx) -> None:
        if ctx is None:
            return
        missing = summarize_required_missing_datasheets(
            ctx.symbols,
            ctx.datasheet_resolutions,
            ai_discovery_results=ctx.ai_discovery_results,
        )
        missing_count = len(missing)
        base = self._tab_labels["datasheets"]
        label = base if missing_count == 0 else f"{base} ({missing_count})"
        idx = ASSISTANT_TAB_IDS.index("datasheets")
        self._notebook.SetPageText(idx, label)

    def _on_char_hook(self, event: wx.KeyEvent) -> None:
        if event.GetModifiers() == wx.MOD_CONTROL:
            key = event.GetKeyCode()
            shortcuts = {
                ord("1"): "chat",
                ord("2"): "datasheets",
                ord("3"): "simulation",
                ord("4"): "aerf",
                ord("5"): "notebook",
                ord("6"): "audits",
                ord("7"): "routing",
            }
            tab_id = shortcuts.get(key)
            if tab_id is not None:
                self.focus_tab(tab_id)
                return
        event.Skip()

    def _on_context_refreshed(self, ctx, summary: str) -> None:
        for tab in self._tabs.values():
            tab.on_context_refreshed(ctx, summary)
        self._update_tab_badges(ctx)

    def _on_tab_changed(self, _event: wx.NotebookEvent) -> None:
        idx = self._notebook.GetSelection()
        if 0 <= idx < len(ASSISTANT_TAB_IDS):
            try:
                pro = normalize_launcher_project_path(self._txt_path.GetValue())
                set_last_tab(pro, ASSISTANT_TAB_IDS[idx])
            except (ValueError, FileNotFoundError, OSError):
                pass
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
    from plugin.assistant_window import show_assistant_window

    show_assistant_window(kicad_parent, project_path, focus_tab=focus_tab)
    run_wx_main_loop_if_needed()
