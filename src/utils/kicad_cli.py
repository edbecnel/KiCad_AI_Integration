"""Discover kicad-cli executable path."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

MACOS_BUNDLE_PATH = Path(
    "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
)


class KicadCliNotFoundError(FileNotFoundError):
    """Raised when kicad-cli cannot be located."""


def resolve_kicad_cli(explicit: str | None = None) -> Path:
    """
    Resolve kicad-cli path.

    Order: explicit argument → KICAD_CLI env → PATH → macOS app bundle.
    """
    candidates: list[Path | str] = []
    if explicit:
        candidates.append(explicit)
    env_cli = os.environ.get("KICAD_CLI")
    if env_cli:
        candidates.append(env_cli)

    which = shutil.which("kicad-cli")
    if which:
        candidates.append(which)

    if sys.platform == "darwin" and MACOS_BUNDLE_PATH.is_file():
        candidates.append(MACOS_BUNDLE_PATH)

    for candidate in candidates:
        path = Path(candidate).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return path.resolve()

    raise KicadCliNotFoundError(
        "kicad-cli not found. Set KICAD_CLI or install KiCad 8+."
    )
