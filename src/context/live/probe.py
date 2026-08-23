"""KiCad live API availability and board access."""

from __future__ import annotations

from typing import Any


def load_pcbnew() -> Any | None:
    """Return the pcbnew module when running inside KiCad."""
    try:
        import pcbnew  # type: ignore[import-untyped]
    except ImportError:
        return None
    return pcbnew


def is_pcbnew_available() -> bool:
    return load_pcbnew() is not None


def get_live_board() -> Any | None:
    """Return the open pcbnew board, if any."""
    pcbnew = load_pcbnew()
    if pcbnew is None:
        return None
    try:
        board = pcbnew.GetBoard()
    except (AttributeError, RuntimeError):
        return None
    if board is None:
        return None
    try:
        if hasattr(board, "IsNull") and board.IsNull():
            return None
    except (AttributeError, RuntimeError):
        pass
    return board


def is_embedded_in_kicad() -> bool:
    """Return True when wx main loop is running (typical KiCad embedding)."""
    try:
        import wx
    except ImportError:
        return False
    app = wx.GetApp()
    return app is not None and app.IsMainLoopRunning()
