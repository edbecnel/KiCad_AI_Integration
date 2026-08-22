"""Launch KiCad AI UI from the Scripting Console or dev shell."""

from __future__ import annotations

from pathlib import Path

# wx.App must stay referenced or it is GC'd before dialogs open (PyNoAppError).
_wx_app: object | None = None


def resolve_project_pro_path(project_path: Path | str | None = None) -> Path:
    """Resolve .kicad_pro from explicit path, directory, or open KiCad board."""
    if project_path is not None:
        path = Path(project_path).expanduser().resolve()
        if path.is_file() and path.suffix == ".kicad_pro":
            return path
        if path.is_dir():
            pros = sorted(path.glob("*.kicad_pro"))
            if pros:
                return pros[0]
        raise FileNotFoundError(f"No .kicad_pro found for {project_path}")

    try:
        import pcbnew  # type: ignore[import-untyped]

        board = pcbnew.GetBoard()
        if board is None:
            raise RuntimeError("No board open in KiCad")
        pcb_path = Path(board.GetFileName())
        if not pcb_path:
            raise RuntimeError("Board has no file name")
        for pro in pcb_path.parent.glob("*.kicad_pro"):
            return pro
    except ImportError as exc:
        raise RuntimeError(
            "No project path given and pcbnew is unavailable (run inside KiCad)"
        ) from exc
    raise FileNotFoundError("No .kicad_pro next to open board")


def try_resolve_project_pro_path(project_path: Path | str | None = None) -> Path | None:
    """
    Resolve .kicad_pro without raising when auto-detection fails.

    When ``project_path`` is omitted, uses the open KiCad board (``pcbnew.GetBoard()``).
    """
    try:
        return resolve_project_pro_path(project_path)
    except (RuntimeError, FileNotFoundError, OSError):
        return None


def effective_initial_project_path(initial_path: Path | str | None = None) -> Path | str | None:
    """Return explicit path or auto-detect from the open KiCad board for UI initialization."""
    if initial_path is not None:
        return initial_path
    return try_resolve_project_pro_path(None)


def ensure_wx_app() -> bool:
    """
    Ensure a wx.App exists before showing UI.

    Returns True when embedded in KiCad (wx main loop already running).
    External scripts must not call ``MainLoop()`` after a modal dialog — ``ShowModal``
    runs until Close; KiCad keeps its own loop alive for the session.
    """
    import wx

    global _wx_app
    app = wx.GetApp()
    if app is None:
        _wx_app = wx.App(False)
        return False
    return app.IsMainLoopRunning()


def run_wx_main_loop_if_needed() -> None:
    """
    Run the wx event loop when launched from an external Terminal.

    No-op when embedded in KiCad (main loop already running). Modal dialogs
    use ``ShowModal()`` and do not need this.
    """
    import wx

    app = wx.GetApp()
    if app is not None and not app.IsMainLoopRunning():
        app.MainLoop()


_KICAD_EDITOR_FRAME_NAMES = ("PcbFrame", "SchematicFrame", "ModEditFrame")
_KICAD_CONSOLE_FRAME_NAMES = frozenset({"KiPython", ""})


def resolve_kicad_parent_window() -> object | None:
    """
    Return the active KiCad editor frame when running inside KiCad.

    Uses the same frame names as KiCad's ``kicad_pyshell`` (``PcbFrame``,
    ``SchematicFrame``). Parenting helps center assistant windows in normal
    windowed mode; macOS full-screen is handled separately in ``kicad_host``.
    """
    import wx

    app = wx.GetApp()
    if app is None or not app.IsMainLoopRunning():
        return None

    for name in _KICAD_EDITOR_FRAME_NAMES:
        frame = wx.FindWindowByName(name)
        if frame is not None:
            return frame

    top = app.GetTopWindow()
    if top is not None:
        window_name = top.GetName()
        if window_name not in _KICAD_CONSOLE_FRAME_NAMES:
            return top
    return None


def resolve_ui_parent(parent: object | None = None) -> object | None:
    """Use explicit parent or auto-detect KiCad editor window when embedded."""
    if parent is not None:
        return parent
    return resolve_kicad_parent_window()


def present_top_level_window(window: object, parent: object | None = None) -> None:
    """Show a frame/dialog, center on parent when embedded, and raise."""
    import wx

    window.Show()
    if parent is not None and isinstance(parent, wx.Window):
        if hasattr(window, "CenterOnParent"):
            window.CenterOnParent()
    window.Raise()
    if hasattr(window, "SetFocus"):
        window.SetFocus()


def show_missing_datasheets_dialog(
    project_path: Path | str | None = None,
    *,
    retry_failed_urls: bool = False,
    force_refresh_urls: bool = False,
    ai_datasheets: bool = False,
) -> None:
    """
    Open the Missing Required Datasheets panel (modal).

    Safe from KiCad Scripting Console or an external Terminal script. When run inside
    KiCad, closing the dialog returns to the editor; KiCad's wx app keeps running.
    When run externally, the Python process exits after Close (no ``MainLoop`` needed).

    KiCad Scripting Console example::

        import sys
        sys.path.insert(0, "/path/to/KiCad_AI_Integration/src")
        from ui.launcher import show_missing_datasheets_dialog
        show_missing_datasheets_dialog()  # uses open board's project
    """
    from ui.missing_datasheets_dialog import show_missing_datasheets_dialog as _show
    from ui.kicad_host import prepare_kicad_ui_launch

    ok, parent = prepare_kicad_ui_launch(None)
    if not ok:
        return
    pro = resolve_project_pro_path(project_path)
    _show(
        pro,
        parent=parent,
        retry_failed_urls=retry_failed_urls,
        force_refresh_urls=force_refresh_urls,
        ai_datasheets=ai_datasheets,
    )


def show_chat_dialog(
    project_path: Path | str | None = None,
    *,
    retry_failed_urls: bool = False,
    force_refresh_urls: bool = False,
) -> None:
    """Open the KiCad AI chat panel (modal)."""
    from ui.chat_dialog import show_chat_dialog as _show
    from ui.kicad_host import prepare_kicad_ui_launch

    ok, parent = prepare_kicad_ui_launch(None)
    if not ok:
        return
    pro = resolve_project_pro_path(project_path)
    _show(
        pro,
        parent=parent,
        retry_failed_urls=retry_failed_urls,
        force_refresh_urls=force_refresh_urls,
    )


def show_simulation_dialog(
    project_path: Path | str | None = None,
) -> None:
    """Open the Simulation models (SUBCKT) panel (modal)."""
    from ui.simulation_dialog import show_simulation_dialog as _show
    from ui.kicad_host import prepare_kicad_ui_launch

    ok, parent = prepare_kicad_ui_launch(None)
    if not ok:
        return
    pro = resolve_project_pro_path(project_path)
    _show(pro, parent=parent)


def show_aerf_dialog(
    project_path: Path | str | None = None,
    *,
    retry_failed_urls: bool = False,
    force_refresh_urls: bool = False,
) -> None:
    """Open the AERF staged analysis panel (modal)."""
    from ui.aerf_dialog import show_aerf_dialog as _show
    from ui.kicad_host import prepare_kicad_ui_launch

    ok, parent = prepare_kicad_ui_launch(None)
    if not ok:
        return
    pro = resolve_project_pro_path(project_path)
    _show(
        pro,
        parent=parent,
        retry_failed_urls=retry_failed_urls,
        force_refresh_urls=force_refresh_urls,
    )


def show_notebook_dialog(
    project_path: Path | str | None = None,
) -> None:
    """Open the Engineering Notebook panel (modal)."""
    from ui.notebook_dialog import show_notebook_dialog as _show
    from ui.kicad_host import prepare_kicad_ui_launch

    ok, parent = prepare_kicad_ui_launch(None)
    if not ok:
        return
    pro = resolve_project_pro_path(project_path)
    _show(pro, parent=parent)


def show_notebook_panel(
    project_path: Path | str | None = None,
) -> None:
    """Open the Engineering Notebook as a non-modal frame (KiCad embedding path)."""
    from ui.notebook_panel import show_notebook_panel as _show
    from ui.kicad_host import prepare_kicad_ui_launch

    ok, parent = prepare_kicad_ui_launch(None)
    if not ok:
        return
    pro = resolve_project_pro_path(project_path)
    _show(pro, parent=parent)


def show_launcher_dialog(
    project_path: Path | str | None = None,
) -> None:
    """Open the KiCad AI Assistant launcher (project picker + panel shortcuts)."""
    from ui.launcher_dialog import show_launcher_dialog as _show
    from ui.kicad_host import prepare_kicad_ui_launch

    ok, parent = prepare_kicad_ui_launch(None)
    if not ok:
        return
    resolved = try_resolve_project_pro_path(project_path)
    _show(resolved if resolved is not None else project_path, parent=parent)


def show_assistant_shell(
    project_path: Path | str | None = None,
    *,
    parent: object | None = None,
    focus_tab: str | None = None,
    open_focus_panel: bool = False,
) -> None:
    """Open the unified Assistant shell (ADP-011)."""
    from ui.assistant_shell import show_assistant_shell as _show
    from ui.kicad_host import prepare_kicad_ui_launch

    ok, resolved_parent = prepare_kicad_ui_launch(parent)
    if not ok:
        return
    resolved = try_resolve_project_pro_path(project_path)
    _show(
        resolved if resolved is not None else project_path,
        parent=resolved_parent,
        focus_tab=focus_tab,
        open_focus_panel=open_focus_panel,
    )
