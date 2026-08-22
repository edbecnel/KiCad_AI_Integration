"""KiCad AI Assistant ActionPlugin package (optional directory install)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _ensure_src_on_path() -> Path | None:
    pkg_dir = Path(__file__).resolve().parent
    candidates = [
        pkg_dir.parent.parent,
        Path(os.environ.get("KICAD_AI_SRC", "")).expanduser(),
    ]
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "ui").is_dir():
            root = str(candidate)
            if root not in sys.path:
                sys.path.insert(0, root)
            return candidate
    return None


_ensure_src_on_path()

try:
    import pcbnew  # type: ignore[import-untyped]

    from kicad_ai_assistant.action_plugin import KiCadAIAssistantPlugin

    if hasattr(pcbnew, "ActionPlugin"):

        class _RegisteredPlugin(KiCadAIAssistantPlugin, pcbnew.ActionPlugin):
            """pcbnew.ActionPlugin subclass registered with KiCad."""

        _instance = _RegisteredPlugin()
        _instance.defaults()
        _instance.register()
except ImportError:
    pass
