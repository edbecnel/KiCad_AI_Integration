"""Minimal PCB summary from .kicad_pcb file (no pcbnew required)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from context.pcb_extract import collect_pcb_detail


def collect_pcb_summary(project_pro_path: Path) -> dict[str, Any] | None:
    """Return footprint/net counts and PCB layout detail when a .kicad_pcb exists."""
    return collect_pcb_detail(project_pro_path)
