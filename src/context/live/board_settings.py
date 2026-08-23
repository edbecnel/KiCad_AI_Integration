"""Live board settings via pcbnew with file-parse fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from context.live.probe import get_live_board
from context.pcb_extract import collect_pcb_detail


def collect_live_board_settings(project_pro_path: Path) -> dict[str, Any]:
    """
    Collect design constraints from the open board when pcbnew is available.

    Falls back to file-based ``collect_pcb_detail`` when pcbnew is unavailable.
    """
    board = get_live_board()
    if board is not None:
        live = _settings_from_board(board)
        if live:
            live["source"] = "pcbnew"
            return live

    file_detail = collect_pcb_detail(project_pro_path)
    if file_detail is None:
        return {"source": None, "available": False}
    return {
        "source": "file",
        "available": True,
        "net_classes": file_detail.get("net_classes"),
        "footprint_count": file_detail.get("footprint_count"),
        "net_count": file_detail.get("net_count"),
        "zone_count": file_detail.get("zone_count"),
    }


def _settings_from_board(board: Any) -> dict[str, Any] | None:
    settings: dict[str, Any] = {"available": True}
    try:
        design = board.GetDesignSettings()
    except (AttributeError, RuntimeError):
        design = None

    if design is not None:
        for attr, key in (
            ("m_TrackWidth", "default_track_width_mm"),
            ("m_ViaDiameter", "default_via_diameter_mm"),
            ("m_ViaDrill", "default_via_drill_mm"),
        ):
            if hasattr(design, attr):
                try:
                    value = getattr(design, attr)
                    if hasattr(value, "AsMM"):
                        settings[key] = float(value.AsMM())
                    else:
                        settings[key] = float(value)
                except (TypeError, ValueError):
                    pass

    try:
        stackup = board.GetBoardStackup()
        if stackup is not None and hasattr(stackup, "GetLayerCount"):
            settings["layer_count"] = int(stackup.GetLayerCount())
    except (AttributeError, RuntimeError, TypeError, ValueError):
        pass

    try:
        settings["footprint_count"] = len(list(board.GetFootprints()))
    except (AttributeError, RuntimeError, TypeError):
        pass

    if len(settings) <= 1:
        return None
    return settings
