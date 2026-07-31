"""KiCad AI Assistant launcher — project picker and panel entry points."""

from __future__ import annotations

from pathlib import Path

from context.collector import collect_stretch_context
from context.datasheet_requirements import format_required_datasheet_notice
from context.simulation_gaps import summarize_simulation_gaps
from context.artifacts.store import ArtifactStore
from prompts.builder import build_prompt_summary
from ui.aerf_dialog import show_aerf_dialog
from ui.chat_dialog import show_chat_dialog
from ui.launcher import ensure_wx_app, resolve_project_pro_path
from ui.missing_datasheets_dialog import show_missing_datasheets_dialog
from ui.notebook_dialog import show_notebook_dialog
from ui.simulation_dialog import show_simulation_dialog
from utils.config import load_config

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


def normalize_launcher_project_path(text: str) -> Path:
    """Resolve a launcher path field to a .kicad_pro file."""
    stripped = text.strip()
    if not stripped:
        raise ValueError("Select a KiCad project (.kicad_pro) or project folder.")
    return resolve_project_pro_path(stripped)


def build_launcher_context_summary(project_path: Path) -> str:
    """Collect project context and format a human-readable status block."""
    cfg = load_config()
    ctx = collect_stretch_context(project_path, config=cfg, verbose=False)
    lines = [build_prompt_summary(ctx, include_image=False)]

    notice = format_required_datasheet_notice(
        ctx.symbols,
        ctx.datasheet_resolutions,
        library_path=cfg.artifact_library_path,
        ai_discovery_results=ctx.ai_discovery_results,
    )
    if notice:
        lines.append("")
        lines.append(notice)

    pro = Path(project_path).expanduser().resolve()
    project_root = pro.parent
    sim_rows = summarize_simulation_gaps(
        ctx.symbols,
        project_root=project_root,
        resolutions=ctx.datasheet_resolutions,
        store=ArtifactStore(cfg.artifact_library_path),
        netlist_text=(
            str(ctx.netlist_summary.get("text"))
            if ctx.netlist_summary and ctx.netlist_summary.get("text")
            else None
        ),
        missing_only=True,
    )
    if sim_rows:
        lines.append("")
        lines.append("--- Simulation models missing ---")
        for row in sim_rows[:12]:
            lines.append(f"  {row.part} ({', '.join(row.references)}): {row.gap_detail}")
        if len(sim_rows) > 12:
            lines.append(f"  … and {len(sim_rows) - 12} more")

    return "\n".join(lines)


class LauncherDialog:
    """Project picker with context refresh and shortcuts to feature panels."""

    def __init__(
        self,
        parent: wx.Window | None,
        initial_path: Path | str | None = None,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for LauncherDialog")
        self._dialog = wx.Dialog(
            parent,
            title="KiCad AI Assistant",
            size=(760, 620),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        panel = wx.Panel(self._dialog)
        vbox = wx.BoxSizer(wx.VERTICAL)

        intro = wx.StaticText(
            panel,
            label=(
                "Choose a KiCad project, refresh context to verify schematic, netlist, "
                "and datasheet collection (standard parts like 1N4007 get simulation "
                "fields automatically), then open a panel."
            ),
        )
        intro.Wrap(700)
        vbox.Add(intro, flag=wx.ALL, border=10)

        path_row = wx.BoxSizer(wx.HORIZONTAL)
        path_row.Add(wx.StaticText(panel, label="Project:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=6)
        self._txt_path = wx.TextCtrl(panel)
        if initial_path:
            try:
                self._txt_path.SetValue(str(resolve_project_pro_path(initial_path)))
            except (FileNotFoundError, OSError):
                self._txt_path.SetValue(str(initial_path))
        path_row.Add(self._txt_path, proportion=1, flag=wx.RIGHT, border=6)
        self._btn_browse_file = wx.Button(panel, label="Browse…")
        self._btn_browse_dir = wx.Button(panel, label="Folder…")
        path_row.Add(self._btn_browse_file, flag=wx.RIGHT, border=4)
        path_row.Add(self._btn_browse_dir)
        vbox.Add(path_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        vbox.Add(wx.StaticText(panel, label="Project context:"), flag=wx.LEFT | wx.TOP, border=8)
        self._summary = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self._summary.SetMinSize((-1, 220))
        vbox.Add(self._summary, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        refresh_row = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_refresh = wx.Button(panel, label="Refresh context")
        self._btn_close = wx.Button(panel, label="Close")
        refresh_row.Add(self._btn_refresh, flag=wx.RIGHT, border=6)
        refresh_row.AddStretchSpacer()
        refresh_row.Add(self._btn_close)
        vbox.Add(refresh_row, flag=wx.EXPAND | wx.ALL, border=8)

        vbox.Add(wx.StaticText(panel, label="Open panel:"), flag=wx.LEFT, border=8)
        panels_row = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_chat = wx.Button(panel, label="Chat")
        self._btn_datasheets = wx.Button(panel, label="Datasheets")
        self._btn_simulation = wx.Button(panel, label="Simulation")
        self._btn_aerf = wx.Button(panel, label="AERF")
        self._btn_notebook = wx.Button(panel, label="Notebook")
        for btn in (
            self._btn_chat,
            self._btn_datasheets,
            self._btn_simulation,
            self._btn_aerf,
            self._btn_notebook,
        ):
            panels_row.Add(btn, flag=wx.RIGHT, border=6)
        vbox.Add(panels_row, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        self._status = wx.StaticText(panel, label="Select a project and click Refresh context.")
        vbox.Add(self._status, flag=wx.ALL, border=8)

        panel.SetSizer(vbox)

        self._btn_browse_file.Bind(wx.EVT_BUTTON, self._on_browse_file)
        self._btn_browse_dir.Bind(wx.EVT_BUTTON, self._on_browse_dir)
        self._btn_refresh.Bind(wx.EVT_BUTTON, self._on_refresh)
        self._btn_close.Bind(wx.EVT_BUTTON, self._on_close)
        self._btn_chat.Bind(wx.EVT_BUTTON, lambda _e: self._open_panel("chat"))
        self._btn_datasheets.Bind(wx.EVT_BUTTON, lambda _e: self._open_panel("datasheets"))
        self._btn_simulation.Bind(wx.EVT_BUTTON, lambda _e: self._open_panel("simulation"))
        self._btn_aerf.Bind(wx.EVT_BUTTON, lambda _e: self._open_panel("aerf"))
        self._btn_notebook.Bind(wx.EVT_BUTTON, lambda _e: self._open_panel("notebook"))

        if initial_path:
            self._on_refresh(None)

    def show_modal(self) -> int:
        return self._dialog.ShowModal()

    def _on_close(self, _event: wx.CommandEvent | None) -> None:
        self._dialog.EndModal(wx.ID_OK)

    def _on_browse_file(self, _event: wx.CommandEvent) -> None:
        dlg = wx.FileDialog(
            self._dialog,
            "Select KiCad project",
            wildcard="KiCad project (*.kicad_pro)|*.kicad_pro",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self._txt_path.SetValue(dlg.GetPath())
        dlg.Destroy()

    def _on_browse_dir(self, _event: wx.CommandEvent) -> None:
        dlg = wx.DirDialog(self._dialog, "Select project folder")
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
        self._dialog.Layout()
        try:
            summary = build_launcher_context_summary(pro)
        except OSError as exc:
            self._status.SetLabel(f"Context error: {exc}")
            return
        self._summary.SetValue(summary)
        self._status.SetLabel(f"Context ready — {pro.name}")

    def _open_panel(self, panel: str) -> None:
        try:
            pro = normalize_launcher_project_path(self._txt_path.GetValue())
        except (ValueError, FileNotFoundError, OSError) as exc:
            wx.MessageBox(str(exc), "KiCad AI Assistant", wx.OK | wx.ICON_WARNING)
            return

        parent = self._dialog
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


def show_launcher_dialog(
    project_path: Path | str | None = None,
    *,
    parent: wx.Window | None = None,
) -> None:
    """Show the KiCad AI Assistant launcher (project picker + panel shortcuts)."""
    if wx is None:
        raise RuntimeError("wxPython is required; run inside KiCad or install wx on PYTHONPATH")
    ensure_wx_app()
    dlg = LauncherDialog(parent, initial_path=project_path)
    dlg.show_modal()

