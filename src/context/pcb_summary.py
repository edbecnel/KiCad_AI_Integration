"""Minimal PCB summary from .kicad_pcb file (no pcbnew required)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def collect_pcb_summary(project_pro_path: Path) -> dict[str, Any] | None:
    """Return footprint/net counts when a matching .kicad_pcb exists."""
    pro = project_pro_path.expanduser().resolve()
    pcb_path = pro.parent / f"{pro.stem}.kicad_pcb"
    if not pcb_path.is_file():
        alts = sorted(pro.parent.glob("*.kicad_pcb"))
        if not alts:
            return None
        pcb_path = alts[0]

    content = pcb_path.read_text(encoding="utf-8", errors="replace")
    footprints = len(re.findall(r"\(footprint\s", content))
    nets = len(re.findall(r'\(net\s+\d+\s+"', content))
    return {
        "pcb_file": pcb_path.name,
        "footprint_count": footprints,
        "net_count": nets,
    }
