"""KiCad ActionPlugin entry — Tools → External Plugins → KiCad AI Assistant."""

from __future__ import annotations

import sys
from pathlib import Path


class KiCadAIAssistantPlugin:
    """Opens the unified Assistant shell as a non-modal frame parented to KiCad."""

    def defaults(self) -> None:
        self.name = "KiCad AI Assistant"
        self.category = "AI Tools"
        self.description = (
            "Open the unified KiCad AI Assistant (Chat, Datasheets, Simulation, AERF, Notebook)."
        )
        self.show_toolbar_button = True
        plugin_dir = Path(__file__).resolve().parent
        icon = plugin_dir / "icon.png"
        dark_icon = plugin_dir / "icon_dark.png"
        if icon.is_file():
            self.icon_file_name = str(icon)
        if dark_icon.is_file():
            self.dark_icon_file_name = str(dark_icon)

    def Run(self) -> None:
        from plugin.bootstrap import ensure_src_on_path

        if ensure_src_on_path() is None:
            self._show_error(
                "KiCad AI source not found on PYTHONPATH.\n\n"
                "Set KICAD_AI_SRC to your repo src/ directory or install the plugin "
                "per docs/Developer_Handbook/01_Development_Environment.md."
            )
            return

        try:
            import wx
        except ImportError:
            self._show_error("wxPython is required but not available in this KiCad build.")
            return

        from plugin.assistant_window import show_assistant_window
        from ui.kicad_host import prepare_kicad_ui_launch
        from ui.launcher import resolve_project_pro_path

        ok, parent = prepare_kicad_ui_launch()
        if not ok:
            return

        try:
            project_path = resolve_project_pro_path()
        except (RuntimeError, FileNotFoundError, OSError) as exc:
            wx.MessageBox(
                f"Could not resolve KiCad project:\n{exc}\n\n"
                "Open a board saved next to a .kicad_pro file, then try again.",
                "KiCad AI Assistant",
                wx.OK | wx.ICON_WARNING,
            )
            return

        show_assistant_window(parent, project_path)

    @staticmethod
    def _show_error(message: str) -> None:
        try:
            import wx

            wx.MessageBox(message, "KiCad AI Assistant", wx.OK | wx.ICON_ERROR)
        except ImportError:
            print(message, file=sys.stderr)
