"""Bootstrap ``src/`` onto ``sys.path`` for KiCad plugin discovery."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def ensure_src_on_path() -> Path | None:
    """Insert the repository ``src/`` directory on ``sys.path`` if needed."""
    plugin_root = Path(__file__).resolve().parent
    candidates = [
        plugin_root.parent,
        plugin_root / "src",
        Path(os.environ.get("KICAD_AI_SRC", "")).expanduser(),
    ]
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "ui").is_dir():
            root = str(candidate)
            if root not in sys.path:
                sys.path.insert(0, root)
            return candidate
    return None
