"""Read project metadata from .kicad_pro JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_project_metadata(pro_path: Path) -> dict[str, Any]:
    """Load project-level metadata from a KiCad .kicad_pro file."""
    pro_path = pro_path.expanduser().resolve()
    project_root = pro_path.parent
    data: dict[str, Any] = {
        "project_file": pro_path.name,
        "project_name": pro_path.stem,
        "project_root": str(project_root),
    }

    if pro_path.is_file():
        try:
            raw = json.loads(pro_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data["kicad_pro"] = {
                    "meta": raw.get("meta"),
                    "text_variables": raw.get("text_variables") or {},
                    "net_settings": raw.get("net_settings") or {},
                }
                sheets = raw.get("sheets") or []
                if sheets:
                    data["sheets"] = sheets
        except (json.JSONDecodeError, OSError):
            data["kicad_pro_error"] = "Could not parse .kicad_pro JSON"

    sch_candidates = sorted(project_root.glob("*.kicad_sch"))
    pcb_candidates = sorted(project_root.glob("*.kicad_pcb"))
    data["schematic_files"] = [p.name for p in sch_candidates]
    data["pcb_files"] = [p.name for p in pcb_candidates]

    root_sch = project_root / f"{pro_path.stem}.kicad_sch"
    if root_sch.is_file():
        data["root_schematic"] = root_sch.name
    elif sch_candidates:
        data["root_schematic"] = sch_candidates[0].name

    root_pcb = project_root / f"{pro_path.stem}.kicad_pcb"
    if root_pcb.is_file():
        data["root_pcb"] = root_pcb.name
    elif pcb_candidates:
        data["root_pcb"] = pcb_candidates[0].name

    return data
