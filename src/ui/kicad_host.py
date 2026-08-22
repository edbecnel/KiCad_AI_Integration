"""KiCad host integration helpers (embedded Scripting Console, macOS UX)."""

from __future__ import annotations

import sys

_MACOS_FULLSCREEN_MESSAGE = (
    "KiCad is in full-screen mode. On macOS, separate assistant windows cannot "
    "display over the PCB editor (this affects KiPython too).\n\n"
    "• Exit full screen: Control+Command+F, then launch again\n"
    "• Or use Terminal (works in any KiCad window mode):\n"
    "  PYTHONPATH=src python scripts/run_ai_assistant.py /path/to/project.kicad_pro --ui\n\n"
    "A dockable in-editor panel is available via the KiCad ActionPlugin (non-modal frame)."
)


def is_embedded_in_kicad() -> bool:
    """True when KiCad's wx main loop is already running (Scripting Console / plugin)."""
    try:
        import wx
    except ImportError:
        return False
    app = wx.GetApp()
    return app is not None and app.IsMainLoopRunning()


def macos_fullscreen_overlay_blocked(parent: object | None = None) -> tuple[bool, str]:
    """
    Return whether macOS full-screen mode blocks overlay UI.

    Parenting to ``PcbFrame`` helps in normal windowed mode but cannot overcome
    macOS Spaces: auxiliary top-level windows (Assistant, KiPython) do not appear
    on top of a full-screen editor.
    """
    if sys.platform != "darwin":
        return False, ""
    if not is_embedded_in_kicad():
        return False, ""

    from ui.launcher import resolve_kicad_parent_window

    editor = parent if parent is not None else resolve_kicad_parent_window()
    if editor is None:
        return False, ""
    if hasattr(editor, "IsFullScreen") and editor.IsFullScreen():
        return True, _MACOS_FULLSCREEN_MESSAGE
    return False, ""


def ensure_ui_can_display_or_warn(parent: object | None = None) -> bool:
    """Show a wx message when macOS full-screen blocks UI; return False to abort launch."""
    blocked, message = macos_fullscreen_overlay_blocked(parent)
    if not blocked:
        return True
    try:
        import wx
    except ImportError:
        return False
    wx.MessageBox(message, "KiCad AI Assistant", wx.OK | wx.ICON_INFORMATION)
    return False


def prepare_kicad_ui_launch(parent: object | None = None) -> tuple[bool, object | None]:
    """
    Prepare wx and resolve parent for in-KiCad UI launch.

    Returns ``(False, None)`` when launch must abort (e.g. macOS full screen).
    """
    from ui.launcher import ensure_wx_app, resolve_ui_parent

    ensure_wx_app()
    resolved = resolve_ui_parent(parent)
    if not ensure_ui_can_display_or_warn(resolved):
        return False, None
    return True, resolved
