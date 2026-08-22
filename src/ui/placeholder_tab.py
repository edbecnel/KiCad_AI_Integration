"""Placeholder Assistant tabs that open legacy modal dialogs (Sprint 1 fallback)."""

from __future__ import annotations

from pathlib import Path

from context.model import ProjectContext
from ui.assistant_tab import AssistantTabPanel
from ui.wx_typing import ModalOpener

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class PlaceholderTab(AssistantTabPanel):
    """Tab with hint text and a button that opens the existing modal panel."""

    def __init__(
        self,
        parent: wx.Window,
        *,
        tab_id: str,
        label: str,
        hint: str,
        open_modal: ModalOpener,
        modal_parent: wx.Window,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for PlaceholderTab")
        super().__init__(parent)
        self._tab_id = tab_id
        self._label = label
        self._open_modal = open_modal
        self._modal_parent = modal_parent
        self._ctx: ProjectContext | None = None

        root = wx.BoxSizer(wx.VERTICAL)
        hint_ctrl = wx.StaticText(self, label=hint)
        hint_ctrl.Wrap(700)
        root.Add(hint_ctrl, flag=wx.ALL, border=10)

        self._open_btn = wx.Button(self, label=f"Open {label} panel")
        self._open_btn.Enable(False)
        self._open_btn.Bind(wx.EVT_BUTTON, self._on_open)
        root.Add(self._open_btn, flag=wx.LEFT | wx.BOTTOM, border=10)
        self.SetSizer(root)

    @property
    def tab_id(self) -> str:
        return self._tab_id

    def on_context_refreshed(self, ctx: ProjectContext, summary: str) -> None:
        self._ctx = ctx
        self._open_btn.Enable(True)

    def open_modal_panel(self) -> None:
        """Open the legacy modal dialog (used by CLI deep links)."""
        self._on_open(None)

    def _on_open(self, _event: wx.CommandEvent | None) -> None:
        if self._ctx is None:
            wx.MessageBox(
                "Refresh context first.",
                "KiCad AI Assistant",
                wx.OK | wx.ICON_WARNING,
            )
            return
        pro = Path(self._ctx.project_path).expanduser().resolve()
        self._open_modal(pro, self._modal_parent)
