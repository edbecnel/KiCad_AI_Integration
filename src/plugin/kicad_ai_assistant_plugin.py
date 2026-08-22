"""KiCad ActionPlugin — single-file entry for scripting/plugins/ (symlink this file).

Install::

    ln -sfn /path/to/KiCad_AI_Integration/src/plugin/kicad_ai_assistant_plugin.py \\
      ~/Documents/KiCad/10.0/scripting/plugins/kicad_ai_assistant.py

KiCad discovers ``*.py`` files in the user plugins directory and calls ``register()``
at import time while the PCB editor is running.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _ensure_src_on_path() -> Path | None:
    """Add repository ``src/`` to ``sys.path`` from this file's location."""
    plugin_file = Path(__file__).resolve()
    candidates = [
        plugin_file.parent.parent,
        Path(os.environ.get("KICAD_AI_SRC", "")).expanduser(),
    ]
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "ui").is_dir():
            root = str(candidate)
            if root not in sys.path:
                sys.path.insert(0, root)
            return candidate
    return None


_SRC_ROOT = _ensure_src_on_path()

try:
    import pcbnew  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    pcbnew = None  # type: ignore[assignment]


if pcbnew is not None and hasattr(pcbnew, "ActionPlugin"):

    class KiCadAIAssistantPlugin(pcbnew.ActionPlugin):
        """Open the unified KiCad AI Assistant shell from the PCB editor."""

        def defaults(self) -> None:
            self.name = "KiCad AI Assistant"
            self.category = "AI Tools"
            self.description = (
                "Open the unified KiCad AI Assistant "
                "(Chat, Datasheets, Simulation, AERF, Notebook)."
            )
            self.show_toolbar_button = True
            assets = Path(__file__).resolve().parent / "kicad_ai_assistant"
            icon = assets / "icon.png"
            dark_icon = assets / "icon_dark.png"
            if icon.is_file():
                self.icon_file_name = str(icon)
            if dark_icon.is_file():
                self.dark_icon_file_name = str(dark_icon)

        def Run(self) -> None:
            if _ensure_src_on_path() is None:
                self._show_error(
                    "KiCad AI source not found on PYTHONPATH.\n\n"
                    "Reinstall the plugin symlink to this repository, or set "
                    "KICAD_AI_SRC to your repo src/ directory."
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

    _plugin = KiCadAIAssistantPlugin()
    _plugin.defaults()
    _plugin.register()
