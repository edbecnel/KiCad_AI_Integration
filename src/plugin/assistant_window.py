"""Singleton non-modal Assistant frame for KiCad plugin and in-editor launch."""

from __future__ import annotations

from pathlib import Path

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]

_assistant_frame: object | None = None


def get_assistant_frame() -> object | None:
    """Return the active Assistant frame, if any."""
    return _assistant_frame


def show_assistant_window(
    parent: object | None = None,
    project_path: Path | str | None = None,
    *,
    focus_tab: str | None = None,
) -> object | None:
    """Show or raise the singleton Assistant frame (non-modal)."""
    if wx is None:
        raise RuntimeError("wxPython is required for show_assistant_window")

    global _assistant_frame
    from ui.assistant_frame import AssistantFrame
    from ui.launcher import present_top_level_window

    frame = _assistant_frame
    if frame is not None:
        try:
            if isinstance(frame, wx.Frame):
                if not frame.IsShown():
                    present_top_level_window(frame, parent)
                else:
                    frame.Raise()
                if focus_tab and hasattr(frame, "focus_tab"):
                    frame.focus_tab(focus_tab)
                return frame
        except RuntimeError:
            _assistant_frame = None

    if frame is not None:
        try:
            frame.Destroy()
        except RuntimeError:
            pass
        _assistant_frame = None

    frame = AssistantFrame(parent, initial_path=project_path, focus_tab=focus_tab)
    frame.Bind(wx.EVT_CLOSE, _on_frame_closed)
    present_top_level_window(frame, parent)
    _assistant_frame = frame
    if focus_tab:
        frame.focus_tab(focus_tab)
    return frame


def _on_frame_closed(event: wx.CloseEvent) -> None:
    global _assistant_frame
    _assistant_frame = None
    event.Skip()


def reset_assistant_window_for_tests() -> None:
    """Clear singleton state (tests only)."""
    global _assistant_frame
    _assistant_frame = None
