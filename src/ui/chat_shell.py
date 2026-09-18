"""Embeddable KiCad AI chat panel (wxPython) with context preview and Approve & Send."""

from __future__ import annotations

import threading
from pathlib import Path

from context.context_cache import save_context_cache
from context.model import ProjectContext
from context.context_flags import ContextIncludeFlags
from conversation.store import get_session_store
from prompts import BuiltPrompt
from providers.errors import ProviderError
from ui.chat_supply import (
    ChatSendResult,
    build_chat_prompt,
    collect_chat_context,
    send_chat_prompt,
)
from inference.chat import build_followup_prompt, prepare_followup_context
from ui.api_key_row import ApiKeyRow
from utils.config import load_config

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]

CHAT_TEMPLATE_IDS = (
    "general_review",
    "pcb_layout_audit",
    "isolation_clearance_audit",
    "netlist_crosscheck",
    "netlist_gap_fill",
    "power_integrity_audit",
    "signal_integrity_audit",
    "emi_emc_audit",
    "flyback_recovery_audit",
)

CHAT_TEMPLATE_LABELS = (
    "General review",
    "PCB layout audit",
    "Isolation / clearance",
    "Netlist crosscheck",
    "Netlist gap-fill",
    "Power integrity",
    "Signal integrity",
    "EMI / EMC",
    "Flyback recovery",
)


class ChatShell(wx.Panel):
    """Embeddable chat panel: preview context, approve, then send to Claude."""

    def __init__(
        self,
        parent: wx.Window,
        project_path: Path,
        *,
        embedded: bool = False,
        retry_failed_urls: bool = False,
        force_refresh_urls: bool = False,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for ChatShell")
        super().__init__(parent)
        self._embedded = embedded
        self._project_path = project_path.expanduser().resolve()
        self._retry_failed_urls = retry_failed_urls
        self._force_refresh_urls = force_refresh_urls
        self._cfg = load_config()
        self._ctx: ProjectContext | None = None
        self._built: BuiltPrompt | None = None
        self._sending = False
        self._conversation_viewer: object | None = None
        self._session_store = get_session_store()
        self._scroll: wx.ScrolledWindow | None = None
        ui_parent: wx.Window = self
        if embedded:
            self._scroll = wx.ScrolledWindow(self, style=wx.VSCROLL)
            self._scroll.SetScrollRate(0, 12)
            ui_parent = self._scroll
        vbox = wx.BoxSizer(wx.VERTICAL)

        api_key_row = ApiKeyRow.create(
            ui_parent,
            initial_value=self._cfg.anthropic_api_key,
        )
        self._api_key_row = api_key_row
        vbox.Add(api_key_row.sizer, flag=wx.EXPAND | wx.ALL, border=8)

        template_row = wx.BoxSizer(wx.HORIZONTAL)
        template_row.Add(wx.StaticText(ui_parent, label="Template:"), flag=wx.RIGHT, border=6)
        self._template_choice = wx.Choice(ui_parent, choices=list(CHAT_TEMPLATE_LABELS))
        self._template_choice.SetSelection(0)
        template_row.Add(self._template_choice, proportion=1)
        template_row.AddStretchSpacer()
        template_row.Add(
            wx.StaticText(
                ui_parent,
                label="Prompt templates — choose a review style before sending.",
            ),
            flag=wx.ALIGN_CENTER_VERTICAL,
        )
        vbox.Add(template_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        self._chk_image = wx.CheckBox(ui_parent, label="Include schematic image")
        vbox.Add(self._chk_image, flag=wx.LEFT | wx.RIGHT, border=8)

        from context.live.probe import is_pcbnew_available

        self._chk_selection = wx.CheckBox(ui_parent, label="Focus on KiCad selection")
        self._chk_selection.Enable(is_pcbnew_available())
        vbox.Add(self._chk_selection, flag=wx.LEFT | wx.RIGHT, border=8)

        fw_row = wx.BoxSizer(wx.HORIZONTAL)
        fw_row.Add(wx.StaticText(ui_parent, label="Firmware file:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=6)
        self._txt_firmware = wx.TextCtrl(ui_parent)
        fw_row.Add(self._txt_firmware, proportion=1, flag=wx.RIGHT, border=6)
        self._btn_firmware = wx.Button(ui_parent, label="Browse…")
        fw_row.Add(self._btn_firmware)
        vbox.Add(fw_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        ctx_row = wx.BoxSizer(wx.HORIZONTAL)
        self._chk_schematic = wx.CheckBox(ui_parent, label="Schematic")
        self._chk_schematic.SetValue(True)
        self._chk_pcb = wx.CheckBox(ui_parent, label="PCB")
        self._chk_pcb.SetValue(True)
        self._chk_bom = wx.CheckBox(ui_parent, label="BOM")
        self._chk_bom.SetValue(True)
        self._chk_erc_drc = wx.CheckBox(ui_parent, label="ERC/DRC")
        self._chk_erc_drc.SetValue(True)
        self._chk_netlist = wx.CheckBox(ui_parent, label="Netlist")
        self._chk_netlist.SetValue(True)
        for chk in (
            self._chk_schematic,
            self._chk_pcb,
            self._chk_bom,
            self._chk_erc_drc,
            self._chk_netlist,
        ):
            ctx_row.Add(chk, flag=wx.RIGHT, border=8)
        vbox.Add(ctx_row, flag=wx.LEFT | wx.RIGHT, border=8)

        vbox.Add(wx.StaticText(ui_parent, label="Design intent (optional):"), flag=wx.LEFT | wx.TOP, border=8)
        self._txt_intent = wx.TextCtrl(ui_parent, style=wx.TE_MULTILINE)
        self._txt_intent.SetMinSize((-1, 48 if not embedded else 36))
        vbox.Add(self._txt_intent, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        vbox.Add(wx.StaticText(ui_parent, label="Your question:"), flag=wx.LEFT | wx.TOP, border=8)
        self._txt_question = wx.TextCtrl(ui_parent, style=wx.TE_MULTILINE)
        self._txt_question.SetMinSize((-1, 56 if not embedded else 40))
        vbox.Add(self._txt_question, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        vbox.Add(wx.StaticText(ui_parent, label="Context preview:"), flag=wx.LEFT | wx.TOP, border=8)
        self._preview = wx.TextCtrl(ui_parent, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self._preview.SetMinSize((-1, 100 if not embedded else 72))
        vbox.Add(self._preview, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        if not self._embedded:
            self._btn_refresh = wx.Button(ui_parent, label="Refresh context")
            btn_row.Add(self._btn_refresh, flag=wx.RIGHT, border=6)
        self._btn_send = wx.Button(ui_parent, label="Approve && Send")
        btn_row.Add(self._btn_send, flag=wx.RIGHT, border=6)
        self._btn_new_conversation = wx.Button(ui_parent, label="New conversation")
        btn_row.Add(self._btn_new_conversation, flag=wx.RIGHT, border=6)
        btn_row.AddStretchSpacer()
        if not self._embedded:
            self._btn_close = wx.Button(ui_parent, label="Close")
            btn_row.Add(self._btn_close)
        vbox.Add(btn_row, flag=wx.EXPAND | wx.ALL, border=8)

        conv_header = wx.BoxSizer(wx.HORIZONTAL)
        conv_header.Add(
            wx.StaticText(ui_parent, label="Conversation:"),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            border=6,
        )
        conv_header.AddStretchSpacer()
        self._btn_expand_conversation = wx.Button(ui_parent, label="Expand…")
        self._btn_expand_conversation.SetToolTip(
            "Open the conversation in a larger resizable window"
        )
        conv_header.Add(self._btn_expand_conversation, flag=wx.LEFT, border=6)
        self._btn_copy_conversation = wx.Button(ui_parent, label="Copy")
        self._btn_copy_conversation.SetToolTip("Copy the full conversation log to the clipboard")
        conv_header.Add(self._btn_copy_conversation, flag=wx.LEFT, border=6)
        self._btn_clear_conversation = wx.Button(ui_parent, label="Clear")
        self._btn_clear_conversation.SetToolTip(
            "Clear the conversation log and reset chat history for this project "
            "(does not clear Your question)"
        )
        conv_header.Add(self._btn_clear_conversation)
        vbox.Add(conv_header, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        self._response = wx.TextCtrl(ui_parent, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self._response.SetMinSize((-1, 120 if embedded else 0))
        vbox.Add(self._response, proportion=0 if embedded else 1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        self._status = wx.StaticText(ui_parent, label="Collect context, review preview, then Approve & Send.")
        vbox.Add(self._status, flag=wx.ALL, border=8)

        if embedded and self._scroll is not None:
            self._scroll.SetSizer(vbox)
            outer = wx.BoxSizer(wx.VERTICAL)
            outer.Add(self._scroll, proportion=1, flag=wx.EXPAND)
            self.SetSizer(outer)
            self.Bind(wx.EVT_SIZE, self._on_embedded_resize)
            self._scroll.FitInside()
        else:
            self.SetSizer(vbox)

        if not self._embedded:
            self._btn_refresh.Bind(wx.EVT_BUTTON, self._on_refresh)
        self._btn_send.Bind(wx.EVT_BUTTON, self._on_send)
        self._btn_new_conversation.Bind(wx.EVT_BUTTON, self._on_new_conversation)
        self._btn_expand_conversation.Bind(wx.EVT_BUTTON, self._on_expand_conversation)
        self._btn_copy_conversation.Bind(wx.EVT_BUTTON, self._on_copy_conversation)
        self._btn_clear_conversation.Bind(wx.EVT_BUTTON, self._on_clear_conversation)
        self._btn_firmware.Bind(wx.EVT_BUTTON, self._on_browse_firmware)
        if not self._embedded:
            self._btn_close.Bind(wx.EVT_BUTTON, self._on_close)
        self._chk_image.Bind(wx.EVT_CHECKBOX, self._on_preview_update)
        self._template_choice.Bind(wx.EVT_CHOICE, self._on_preview_update)
        for chk in (
            self._chk_schematic,
            self._chk_pcb,
            self._chk_bom,
            self._chk_erc_drc,
            self._chk_netlist,
        ):
            chk.Bind(wx.EVT_CHECKBOX, self._on_preview_update)

        if not self._embedded:
            self._refresh_context()

    def _on_embedded_resize(self, event: wx.Event) -> None:
        if self._scroll is not None:
            self._scroll.FitInside()
        event.Skip()

    def apply_context(self, ctx: ProjectContext) -> None:
        """Use project context from the Assistant shell header."""
        self._ctx = self._apply_live_options(ctx)
        self._update_preview()
        self._refresh_conversation_log()
        self._status.SetLabel("Context ready — review preview, then Approve & Send.")

    def _firmware_path_value(self) -> str | None:
        value = self._txt_firmware.GetValue().strip()
        return value or None

    def _apply_live_options(self, ctx: ProjectContext) -> ProjectContext:
        from context.live.enrich import enrich_live_context

        return enrich_live_context(
            ctx,
            self._project_path,
            config=self._cfg,
            use_selection=self._chk_selection.GetValue(),
            firmware_path=self._firmware_path_value(),
        )

    def _on_browse_firmware(self, _event: wx.CommandEvent) -> None:
        dlg = wx.FileDialog(
            self,
            "Select firmware source file",
            wildcard="All files (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self._txt_firmware.SetValue(dlg.GetPath())
            if self._ctx is not None:
                self._ctx = self._apply_live_options(self._ctx)
                self._update_preview()
        dlg.Destroy()

    def _session(self):
        return self._session_store.get_or_create(self._project_path)

    def _conversation_log_text(self) -> str:
        return self._session().format_conversation_log()

    def _refresh_conversation_log(self) -> None:
        text = self._conversation_log_text()
        self._response.SetValue(text)
        self._sync_conversation_viewer(text)

    def _sync_conversation_viewer(self, text: str) -> None:
        viewer = self._conversation_viewer
        if viewer is None:
            return
        try:
            from ui.conversation_viewer import ConversationViewerFrame

            if isinstance(viewer, ConversationViewerFrame) and viewer.IsShown():
                viewer.set_content(text)
        except RuntimeError:
            self._conversation_viewer = None

    def _on_expand_conversation(self, _event: wx.CommandEvent) -> None:
        from ui.conversation_viewer import ConversationViewerFrame, show_conversation_viewer

        text = self._conversation_log_text()
        placeholder = "(No messages yet — send a question to start the conversation.)"
        viewer = self._conversation_viewer
        if isinstance(viewer, ConversationViewerFrame):
            try:
                if viewer.IsShown():
                    viewer.set_content(text or placeholder)
                    viewer.Raise()
                    return
            except RuntimeError:
                self._conversation_viewer = None

        def on_closed() -> None:
            self._conversation_viewer = None

        save_name = f"{self._project_path.stem}_conversation.md"
        self._conversation_viewer = show_conversation_viewer(
            self,
            text or placeholder,
            refresh_callback=self._conversation_log_text,
            markdown_callback=lambda: self._session().format_conversation_markdown(),
            default_save_name=save_name,
            on_closed=on_closed,
        )

    def _on_clear_conversation(self, _event: wx.CommandEvent) -> None:
        if self._sending:
            return
        if self._session().turns and wx.MessageBox(
            "Clear the conversation log? Chat history for this project will be reset "
            "and follow-up requests will not include prior turns.",
            "Clear conversation",
            wx.YES_NO | wx.ICON_QUESTION,
        ) != wx.YES:
            return
        self._session_store.reset(self._project_path)
        self._refresh_conversation_log()
        self._status.SetLabel("Conversation cleared — enter a question, then Approve & Send.")

    def _on_copy_conversation(self, _event: wx.CommandEvent) -> None:
        text = self._response.GetValue()
        if not text.strip():
            self._status.SetLabel("Nothing to copy — conversation is empty.")
            return
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()
            self._status.SetLabel("Conversation copied to clipboard.")
        else:
            self._status.SetLabel("Could not open clipboard.")

    def _on_new_conversation(self, _event: wx.CommandEvent) -> None:
        if self._sending:
            return
        if self._session().turns and wx.MessageBox(
            "Start a new conversation? Current session history will be cleared.",
            "New conversation",
            wx.YES_NO | wx.ICON_QUESTION,
        ) != wx.YES:
            return
        self._session_store.reset(self._project_path)
        self._refresh_conversation_log()
        self._txt_question.SetValue("")
        self._status.SetLabel("New conversation — enter a question, then Approve & Send.")

    def confirm_close(self) -> bool:
        return True

    def _selected_template(self) -> str:
        idx = self._template_choice.GetSelection()
        if idx < 0 or idx >= len(CHAT_TEMPLATE_IDS):
            return CHAT_TEMPLATE_IDS[0]
        return CHAT_TEMPLATE_IDS[idx]

    def export_ui_state(self) -> dict[str, object]:
        # Ensure pending edits in multiline fields are flushed (macOS wx).
        self._txt_intent.Update()
        self._txt_question.Update()
        return {
            "template": self._selected_template(),
            "include_schematic_image": self._chk_image.GetValue(),
            "focus_selection": self._chk_selection.GetValue(),
            "firmware_file": self._txt_firmware.GetValue(),
            "include_schematic": self._chk_schematic.GetValue(),
            "include_pcb": self._chk_pcb.GetValue(),
            "include_bom": self._chk_bom.GetValue(),
            "include_erc_drc": self._chk_erc_drc.GetValue(),
            "include_netlist": self._chk_netlist.GetValue(),
            "design_intent": self._txt_intent.GetValue(),
            "question_draft": self._txt_question.GetValue(),
        }

    def apply_ui_state(self, data: dict[str, object]) -> None:
        template = str(data.get("template", CHAT_TEMPLATE_IDS[0]))
        if template in CHAT_TEMPLATE_IDS:
            self._template_choice.SetSelection(CHAT_TEMPLATE_IDS.index(template))
        self._chk_image.SetValue(bool(data.get("include_schematic_image", False)))
        if self._chk_selection.IsEnabled():
            self._chk_selection.SetValue(bool(data.get("focus_selection", False)))
        self._txt_firmware.SetValue(str(data.get("firmware_file", "")))
        self._chk_schematic.SetValue(bool(data.get("include_schematic", True)))
        self._chk_pcb.SetValue(bool(data.get("include_pcb", True)))
        self._chk_bom.SetValue(bool(data.get("include_bom", True)))
        self._chk_erc_drc.SetValue(bool(data.get("include_erc_drc", True)))
        self._chk_netlist.SetValue(bool(data.get("include_netlist", True)))
        self._txt_intent.SetValue(str(data.get("design_intent", "")))
        self._txt_question.SetValue(str(data.get("question_draft", "")))
        if self._ctx is not None:
            self._ctx = self._apply_live_options(self._ctx)
            self._update_preview()

    def _context_flags(self) -> ContextIncludeFlags:
        return ContextIncludeFlags(
            schematic=self._chk_schematic.GetValue(),
            pcb=self._chk_pcb.GetValue(),
            bom=self._chk_bom.GetValue(),
            erc_drc=self._chk_erc_drc.GetValue(),
            netlist=self._chk_netlist.GetValue(),
        )

    def _on_close(self, _event: wx.CommandEvent) -> None:
        top = self.GetTopLevelParent()
        if hasattr(top, "EndModal"):
            top.EndModal(wx.ID_OK)

    def _on_refresh(self, _event: wx.CommandEvent) -> None:
        if not self._embedded:
            self._refresh_context()

    def _on_preview_update(self, _event: wx.CommandEvent) -> None:
        if self._ctx is not None:
            self._update_preview()

    def _refresh_context(self) -> None:
        self._status.SetLabel("Collecting context…")
        self.Layout()
        try:
            self._ctx = collect_chat_context(
                self._project_path,
                config=self._cfg,
                include_image=self._chk_image.GetValue(),
                retry_failed_urls=self._retry_failed_urls,
                force_refresh_urls=self._force_refresh_urls,
                verbose=False,
            )
        except OSError as exc:
            self._status.SetLabel(f"Context error: {exc}")
            return
        if self._ctx is not None and self._chk_image.GetValue():
            err = self._ctx.schematic_image_error
            if err:
                self._status.SetLabel(f"Schematic image unavailable: {err}")
            elif self._unsaved_schematic_warning():
                self._status.SetLabel(
                    "Context ready — schematic file newer than project; save in KiCad before image export."
                )
                self._update_preview()
                return
        self._update_preview()
        if self._ctx is not None and self._ctx.schematic_image_error and self._chk_image.GetValue():
            return
        self._status.SetLabel("Context ready — review preview, then Approve & Send.")

    def _unsaved_schematic_warning(self) -> bool:
        if self._ctx is None:
            return False
        pro = self._project_path
        sch = pro.with_suffix(".kicad_sch")
        if not sch.is_file() or not pro.is_file():
            return False
        return sch.stat().st_mtime > pro.stat().st_mtime

    def _update_preview(self) -> None:
        if self._ctx is None:
            return
        question = self._txt_question.GetValue().strip() or "(enter a question)"
        built = build_chat_prompt(
            self._ctx,
            question,
            functional_description=self._txt_intent.GetValue().strip() or None,
            include_image=self._chk_image.GetValue(),
            include=self._context_flags(),
            template=self._selected_template(),
        )
        self._built = built
        preview_text = (
            f"{built.preview_summary}\n\n"
            f"Estimated text tokens: ~{built.estimated_text_tokens}\n"
            f"Template: {built.template}\n\n"
            "--- Prompt excerpt (first 1200 chars) ---\n"
            f"{built.text[:1200]}"
        )
        if len(built.text) > 1200:
            preview_text += "\n…"
        self._preview.SetValue(preview_text)

    def _on_send(self, _event: wx.CommandEvent) -> None:
        if self._sending:
            return
        question = self._txt_question.GetValue().strip()
        if not question:
            wx.MessageBox("Enter a question first.", "KiCad AI", wx.OK | wx.ICON_INFORMATION)
            return
        if self._ctx is None:
            self._refresh_context()
        if self._ctx is None:
            return
        self._ctx = self._apply_live_options(self._ctx)

        session = self._session()
        is_followup = bool(session.turns)
        dirty_layers: set[str] = set()
        cache_entry = None
        if is_followup:
            self._ctx, dirty_layers, cache_entry = prepare_followup_context(
                self._ctx,  # type: ignore[arg-type]
                self._project_path,
                config=self._cfg,
                include_flags=self._context_flags(),
                include_image=self._chk_image.GetValue(),
            )
            if dirty_layers:
                self._status.SetLabel(
                    f"Project changed — refreshed: {', '.join(sorted(dirty_layers))}"
                )
                self.Layout()

        approve_text = (
            "Send this follow-up question to Anthropic?\n\n"
            "Prior conversation turns will be included."
            if is_followup
            else "Send this context and question to Anthropic?\n\n"
            "Review the preview above before approving."
        )
        if wx.MessageBox(
            approve_text,
            "Approve transmission",
            wx.YES_NO | wx.ICON_QUESTION,
        ) != wx.YES:
            return

        self._sending = True
        self._btn_send.Enable(False)
        if not self._embedded:
            self._btn_refresh.Enable(False)

        intent = self._txt_intent.GetValue().strip() or None
        template = self._selected_template()
        if is_followup:
            built = build_followup_prompt(
                self._ctx,
                question,
                functional_description=intent,
                template=template,
                project_path=self._project_path,
                dirty_layers=dirty_layers,
                cache_entry=cache_entry,
            )
        else:
            built = build_chat_prompt(
                self._ctx,
                question,
                functional_description=intent,
                include_image=self._chk_image.GetValue(),
                include=self._context_flags(),
                template=template,
            )
        api_key = self._api_key_row.get_value().strip() or None
        approx_mb = (len(built.text) + built.image_byte_size) / (1024 * 1024)
        if built.include_image:
            self._status.SetLabel(
                f"Sending ~{approx_mb:.1f} MB (image + context) — "
                f"may take 2–6 min; read timeout {self._cfg.provider_read_timeout_sec}s…"
            )
        else:
            self._status.SetLabel("Sending to Claude…")
        self.Layout()

        threading.Thread(
            target=self._send_in_background,
            args=(built, question, api_key),
            daemon=True,
        ).start()

    def _send_in_background(
        self,
        built: BuiltPrompt,
        question: str,
        api_key: str | None,
    ) -> None:
        session = self._session()
        try:
            result = send_chat_prompt(
                built,
                self._ctx,  # type: ignore[arg-type]
                config=self._cfg,
                api_key_override=api_key,
                session=session,
            )
        except ProviderError as exc:
            wx.CallAfter(self._on_send_failed, exc)
            return
        wx.CallAfter(self._on_send_succeeded, result, question, built.text)

    def _on_send_failed(self, exc: ProviderError) -> None:
        self._sending = False
        self._btn_send.Enable(True)
        if not self._embedded:
            self._btn_refresh.Enable(True)
        self._status.SetLabel(f"Provider error: {exc}")
        wx.MessageBox(str(exc), "Provider error", wx.OK | wx.ICON_ERROR)

    def _on_send_succeeded(
        self,
        result: ChatSendResult,
        question: str,
        api_content: str,
    ) -> None:
        session = self._session()
        session.append_user(question, api_content=api_content)
        session.append_assistant(
            result.response.text,
            input_tokens=result.response.usage.input_tokens,
            output_tokens=result.response.usage.output_tokens,
            model=result.response.model,
        )
        self._session_store.save(self._project_path)
        if session.user_turn_count == 1:
            save_context_cache(
                self._project_path,
                self._ctx,  # type: ignore[arg-type]
                prompt_excerpt=api_content[:2000] if api_content else None,
            )
        self._sending = False
        self._btn_send.Enable(True)
        if not self._embedded:
            self._btn_refresh.Enable(True)
        self._txt_question.SetValue("")
        self._refresh_conversation_log()
        self._status.SetLabel(
            f"Turn {session.user_turn_count} — "
            f"{result.response.usage.input_tokens} in, "
            f"{result.response.usage.output_tokens} out tokens "
            f"({result.response.model}). Ask a follow-up or start a new conversation."
        )
