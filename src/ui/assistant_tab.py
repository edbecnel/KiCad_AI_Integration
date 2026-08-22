"""Assistant shell tab panel protocol (ADP-011 §7)."""

from __future__ import annotations

from context.model import ProjectContext

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]

ASSISTANT_TAB_IDS = ("chat", "datasheets", "simulation", "aerf", "notebook")


def tab_index_for_focus(focus_tab: str | None, tab_ids: tuple[str, ...] = ASSISTANT_TAB_IDS) -> int | None:
    """Map a focus_tab id to a notebook page index, or None if unknown."""
    if focus_tab and focus_tab in tab_ids:
        return tab_ids.index(focus_tab)
    return None


class AssistantTabPanel(wx.Panel):
    """Base class for embedded Assistant shell tabs."""

    def on_context_refreshed(self, ctx: ProjectContext, summary: str) -> None:
        """Called when the shared header refreshes project context."""

    def on_tab_selected(self) -> None:
        """Called when this tab becomes active (optional lazy load)."""

    def confirm_discard(self) -> bool:
        """Return False to veto shell close when this tab has unsaved edits."""
        return True

    def _hide_placeholder(self) -> None:
        """Drop the idle-state label from layout so it cannot paint over the shell."""
        sizer = self.GetSizer()
        if sizer is not None:
            sizer.Hide(self._placeholder)
        self._placeholder.Hide()

    def _show_placeholder(self) -> None:
        """Restore the idle-state label after the embedded shell is torn down."""
        sizer = self.GetSizer()
        if sizer is not None:
            sizer.Show(self._placeholder)
        self._placeholder.Show()
