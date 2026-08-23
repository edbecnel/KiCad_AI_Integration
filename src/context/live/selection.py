"""Selected PCB objects from pcbnew for focused chat context."""

from __future__ import annotations

from typing import Any

from context.live.probe import get_live_board


def collect_selection_context() -> dict[str, Any]:
    """Return selected footprints and nets from the open board."""
    board = get_live_board()
    if board is None:
        return {"available": False, "footprints": [], "nets": []}

    footprints: list[dict[str, str]] = []
    nets: list[str] = []

    try:
        selected = board.GetCurrentSelection()
    except (AttributeError, RuntimeError):
        selected = []

    if selected:
        for item in selected:
            ref = _footprint_reference(item)
            if ref:
                footprints.append(ref)
            net_name = _net_name(item)
            if net_name and net_name not in nets:
                nets.append(net_name)

    if not footprints:
        footprints = _selected_footprints_fallback(board)

    return {
        "available": bool(footprints or nets),
        "footprints": footprints[:40],
        "nets": nets[:40],
    }


def _footprint_reference(item: Any) -> dict[str, str] | None:
    try:
        if hasattr(item, "GetReference"):
            ref = str(item.GetReference())
            value = str(item.GetValue()) if hasattr(item, "GetValue") else ""
            return {"reference": ref, "value": value}
    except (AttributeError, RuntimeError, TypeError):
        return None
    return None


def _net_name(item: Any) -> str | None:
    try:
        if hasattr(item, "GetNetname"):
            name = str(item.GetNetname())
            return name if name else None
    except (AttributeError, RuntimeError, TypeError):
        return None
    return None


def _selected_footprints_fallback(board: Any) -> list[dict[str, str]]:
    """Best-effort selection via footprint IsSelected when GetCurrentSelection missing."""
    out: list[dict[str, str]] = []
    try:
        for fp in board.GetFootprints():
            if hasattr(fp, "IsSelected") and fp.IsSelected():
                ref = _footprint_reference(fp)
                if ref:
                    out.append(ref)
    except (AttributeError, RuntimeError, TypeError):
        return []
    return out
