"""Embedded Chat tab for the Assistant shell."""

from __future__ import annotations

from pathlib import Path

from context.model import ProjectContext
from ui.assistant_tab import AssistantTabPanel
from ui.chat_shell import ChatShell
from ui.session_state import normalize_tab_session_block

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class ChatTab(AssistantTabPanel):
    """Hosts ChatShell inline."""

    HELP_TOPIC_ID = "chat"

    def __init__(self, parent: wx.Window) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for ChatTab")
        super().__init__(parent)
        self._loaded_path: Path | None = None
        self._shell: ChatShell | None = None
        self._pending_chat_ui_state: dict[str, object] | None = None
        self._session_ui_state: dict[str, object] | None = None
        self._session_ui_for_path: Path | None = None

        self._placeholder = wx.StaticText(
            self,
            label="Select a project and click Refresh context to use Chat.",
        )
        self._placeholder.Wrap(700)

        self._shell_slot = wx.Panel(self)
        self._shell_sizer = wx.BoxSizer(wx.VERTICAL)
        self._shell_slot.SetSizer(self._shell_sizer)

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(self.build_help_row(), flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=4)
        root.Add(self._placeholder, flag=wx.ALL, border=10)
        root.Add(self._shell_slot, proportion=1, flag=wx.EXPAND)
        self.SetSizer(root)

    def on_context_refreshed(self, ctx: ProjectContext, summary: str) -> None:
        new_path = Path(ctx.project_path).expanduser().resolve()
        if self._shell is not None and self._loaded_path == new_path:
            self._shell.apply_context(ctx)
            self._apply_deferred_chat_ui_state()
            return
        if self._shell is not None:
            self._clear_shell()
            if self._session_ui_for_path != new_path:
                self._session_ui_state = None

        self._loaded_path = new_path
        self._hide_placeholder()
        self._shell = ChatShell(self._shell_slot, new_path, embedded=True)
        self._shell_sizer.Add(self._shell, proportion=1, flag=wx.EXPAND)
        self._shell.apply_context(ctx)
        self._apply_deferred_chat_ui_state()
        self._shell_slot.Layout()
        self.Layout()

    def export_session_state(self) -> dict[str, object]:
        if self._shell is None:
            return {}
        return self._shell.export_ui_state()

    def import_session_state(
        self,
        data: dict[str, object],
        *,
        project_path: Path | None = None,
    ) -> None:
        block = normalize_tab_session_block(data, nested_key="chat")
        if block is None:
            return
        if project_path is not None:
            self._session_ui_for_path = project_path.expanduser().resolve()
        elif self._loaded_path is not None:
            self._session_ui_for_path = self._loaded_path
        self._session_ui_state = block
        self._pending_chat_ui_state = block
        self._apply_deferred_chat_ui_state()

    def _apply_deferred_chat_ui_state(self) -> None:
        if self._shell is None or self._loaded_path is None:
            return
        if (
            self._session_ui_for_path is not None
            and self._session_ui_for_path != self._loaded_path
        ):
            return
        block = self._session_ui_state or self._pending_chat_ui_state
        if block is None:
            return
        self._shell.apply_ui_state(block)
        self._pending_chat_ui_state = None

    def _clear_shell(self) -> None:
        if self._shell is not None:
            self._shell.Destroy()
            self._shell = None
        self._shell_sizer.Clear(False)
        self._loaded_path = None
        self._show_placeholder()
