"""Phase 2 native plugin entry points.

Install ``kicad_ai_assistant/`` into KiCad's ``scripting/plugins/`` directory.
See ``docs/Developer_Handbook/01_Development_Environment.md``.
"""

from plugin.assistant_window import get_assistant_frame, show_assistant_window

__all__ = ["get_assistant_frame", "show_assistant_window"]
