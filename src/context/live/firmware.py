"""Optional external firmware file context for cross-review."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_MAX_BYTES = 32_000


def load_firmware_summary(firmware_path: Path | str | None) -> dict[str, Any] | None:
    """Load a text firmware file into a compact summary block."""
    if not firmware_path:
        return None
    path = Path(firmware_path).expanduser()
    if not path.is_file():
        return {"available": False, "path": str(path), "error": "File not found"}

    try:
        raw = path.read_bytes()
    except OSError as exc:
        return {"available": False, "path": str(path), "error": str(exc)}

    truncated = len(raw) > _MAX_BYTES
    text = raw[:_MAX_BYTES].decode("utf-8", errors="replace")
    return {
        "available": True,
        "path": str(path.resolve()),
        "byte_size": len(raw),
        "truncated": truncated,
        "text": text,
    }


def project_settings_path(project_path: Path | str) -> Path:
    """Per-project UI settings under ``kicad_ai/settings.json``."""
    pro = Path(project_path).expanduser().resolve()
    return pro.parent / "kicad_ai" / "settings.json"
