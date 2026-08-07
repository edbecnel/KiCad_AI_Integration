"""PCB detail extraction from .kicad_pcb (no pcbnew required)."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any


def _resolve_pcb_path(project_pro_path: Path) -> Path | None:
    pro = project_pro_path.expanduser().resolve()
    pcb_path = pro.parent / f"{pro.stem}.kicad_pcb"
    if pcb_path.is_file():
        return pcb_path
    alts = sorted(pro.parent.glob("*.kicad_pcb"))
    return alts[0] if alts else None


def _parse_net_names(content: str) -> dict[int, str]:
    names: dict[int, str] = {}
    for match in re.finditer(r'\(net\s+(\d+)\s+"([^"]*)"', content):
        names[int(match.group(1))] = match.group(2)
    return names


def _parse_net_classes(content: str) -> list[dict[str, Any]]:
    classes: list[dict[str, Any]] = []
    pattern = re.compile(
        r'\(net_class\s+"([^"]+)"(.*?)\)\s*\n',
        re.DOTALL,
    )
    for match in pattern.finditer(content):
        name = match.group(1)
        body = match.group(2)
        clearance = re.search(r"\(clearance\s+([\d.]+)", body)
        track_width = re.search(r"\(track_width\s+([\d.]+)", body)
        classes.append(
            {
                "name": name,
                "clearance_mm": float(clearance.group(1)) if clearance else None,
                "track_width_mm": float(track_width.group(1)) if track_width else None,
            }
        )
    return classes


def collect_pcb_detail(project_pro_path: Path) -> dict[str, Any] | None:
    """Extract tracks, vias, zones, and net classes from a KiCad PCB file."""
    pcb_path = _resolve_pcb_path(project_pro_path)
    if pcb_path is None:
        return None

    content = pcb_path.read_text(encoding="utf-8", errors="replace")
    net_names = _parse_net_names(content)

    tracks: list[dict[str, Any]] = []
    segment_re = re.compile(
        r"\(segment\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\)"
        r"(.*?)\)\s*\n",
        re.DOTALL,
    )
    for match in segment_re.finditer(content):
        x1, y1, x2, y2 = (float(match.group(i)) for i in range(1, 5))
        body = match.group(5)
        width_m = re.search(r"\(width\s+([\d.]+)", body)
        layer_m = re.search(r'\(layer\s+"([^"]+)"', body)
        net_m = re.search(r"\(net\s+(\d+)", body)
        width = float(width_m.group(1)) if width_m else None
        layer = layer_m.group(1) if layer_m else None
        net_id = int(net_m.group(1)) if net_m else None
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        tracks.append(
            {
                "layer": layer,
                "net": net_names.get(net_id, f"net_{net_id}") if net_id is not None else None,
                "width_mm": width,
                "length_mm": round(length, 4),
            }
        )

    vias: list[dict[str, Any]] = []
    via_re = re.compile(r"\(via\s+(.*?)\)\s*\n", re.DOTALL)
    for match in via_re.finditer(content):
        body = match.group(1)
        size_m = re.search(r"\(size\s+([\d.]+)", body)
        drill_m = re.search(r"\(drill\s+([\d.]+)", body)
        layers_m = re.search(r'\(layers\s+"([^"]+)"', body)
        net_m = re.search(r"\(net\s+(\d+)", body)
        net_id = int(net_m.group(1)) if net_m else None
        vias.append(
            {
                "net": net_names.get(net_id, f"net_{net_id}") if net_id is not None else None,
                "size_mm": float(size_m.group(1)) if size_m else None,
                "drill_mm": float(drill_m.group(1)) if drill_m else None,
                "layers": layers_m.group(1) if layers_m else None,
            }
        )

    zones = len(re.findall(r"\(zone\s", content))
    footprints = len(re.findall(r"\(footprint\s", content))

    per_net_length: dict[str, float] = defaultdict(float)
    for t in tracks:
        if t.get("net"):
            per_net_length[str(t["net"])] += float(t["length_mm"])

    net_totals = [
        {"net": net, "total_length_mm": round(total, 4)}
        for net, total in sorted(per_net_length.items(), key=lambda x: -x[1])
    ]

    return {
        "pcb_file": pcb_path.name,
        "footprint_count": footprints,
        "net_count": len(net_names),
        "track_segment_count": len(tracks),
        "via_count": len(vias),
        "zone_count": zones,
        "net_classes": _parse_net_classes(content),
        "tracks_sample": tracks[:50],
        "vias_sample": vias[:30],
        "net_track_totals": net_totals[:40],
    }
