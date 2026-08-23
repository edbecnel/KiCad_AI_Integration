"""Active editor paths from the open KiCad board."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from context.live.probe import get_live_board


def collect_editor_context() -> dict[str, Any]:
    """Return paths for the open board/project when pcbnew is available."""
    board = get_live_board()
    if board is None:
        return {"available": False}

    pcb_path: Path | None = None
    try:
        name = board.GetFileName()
        if name:
            pcb_path = Path(name).expanduser().resolve()
    except (AttributeError, OSError, RuntimeError, TypeError):
        pcb_path = None

    pro_path: Path | None = None
    if pcb_path is not None and pcb_path.is_file():
        for candidate in sorted(pcb_path.parent.glob("*.kicad_pro")):
            if candidate.stem == pcb_path.stem:
                pro_path = candidate
                break
        if pro_path is None:
            pros = sorted(pcb_path.parent.glob("*.kicad_pro"))
            pro_path = pros[0] if pros else None

    schematic_paths: list[str] = []
    if pro_path is not None:
        from context.schematic_parse import discover_schematic_paths

        schematic_paths = [str(p) for p in discover_schematic_paths(pro_path)]

    return {
        "available": True,
        "pcb_path": str(pcb_path) if pcb_path else None,
        "project_path": str(pro_path) if pro_path else None,
        "schematic_paths": schematic_paths,
    }
