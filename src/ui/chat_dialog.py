"""KiCad AI chat panel (wxPython) with context preview and Approve & Send."""

from __future__ import annotations

import threading
from pathlib import Path

from context.model import ProjectContext
from context.context_flags import ContextIncludeFlags
from prompts import BuiltPrompt
from providers.errors import ProviderError
from ui.chat_supply import (
    ChatSendResult,
    build_chat_prompt,
    collect_chat_context,
    send_chat_prompt,
)
from utils.config import AppConfig, load_config

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class ChatDialog:
    """Modal chat dialog: preview context, approve, then send to Claude."""

    def __init__(
        self,
        parent: wx.Window | None,
        project_path: Path,
        *,
        retry_failed_urls: bool = False,
        force_refresh_urls: bool = False,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for ChatDialog")
        self._project_path = project_path.expanduser().resolve()
        self._retry_failed_urls = retry_failed_urls
        self._force_refresh_urls = force_refresh_urls
        self._cfg = load_config()
        self._ctx: ProjectContext | None = None
        self._built: BuiltPrompt | None = None
        self._approved = False

        self._dialog = wx.Dialog(
            parent,
            title="KiCad AI Assistant",
            size=(780, 640),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        panel = wx.Panel(self._dialog)
        vbox = wx.BoxSizer(wx.VERTICAL)

        key_row = wx.BoxSizer(wx.HORIZONTAL)
        key_row.Add(wx.StaticText(panel, label="API key:"), flag=wx.RIGHT, border=6)
        self._txt_key = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        if self._cfg.anthropic_api_key:
            self._txt_key.SetValue(self._cfg.anthropic_api_key)
        key_row.Add(self._txt_key, proportion=1)
        vbox.Add(key_row, flag=wx.EXPAND | wx.ALL, border=8)

        template_row = wx.BoxSizer(wx.HORIZONTAL)
        template_row.Add(wx.StaticText(panel, label="Template:"), flag=wx.RIGHT, border=6)
        self._template_choice = wx.Choice(
            panel,
            choices=[
                "General review",
                "PCB layout audit",
                "Isolation / clearance",
                "Netlist crosscheck",
                "Netlist gap-fill",
            ],
        )
        self._template_choice.SetSelection(0)
        template_row.Add(self._template_choice, proportion=1)
        vbox.Add(template_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        self._chk_image = wx.CheckBox(panel, label="Include schematic image")
        vbox.Add(self._chk_image, flag=wx.LEFT | wx.RIGHT, border=8)

        ctx_row = wx.BoxSizer(wx.HORIZONTAL)
        self._chk_schematic = wx.CheckBox(panel, label="Schematic")
        self._chk_schematic.SetValue(True)
        self._chk_pcb = wx.CheckBox(panel, label="PCB")
        self._chk_pcb.SetValue(True)
        self._chk_bom = wx.CheckBox(panel, label="BOM")
        self._chk_bom.SetValue(True)
        self._chk_erc_drc = wx.CheckBox(panel, label="ERC/DRC")
        self._chk_erc_drc.SetValue(True)
        self._chk_netlist = wx.CheckBox(panel, label="Netlist")
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

        vbox.Add(wx.StaticText(panel, label="Design intent (optional):"), flag=wx.LEFT | wx.TOP, border=8)
        self._txt_intent = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self._txt_intent.SetMinSize((-1, 48))
        vbox.Add(self._txt_intent, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        vbox.Add(wx.StaticText(panel, label="Your question:"), flag=wx.LEFT | wx.TOP, border=8)
        self._txt_question = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self._txt_question.SetMinSize((-1, 56))
        vbox.Add(self._txt_question, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        vbox.Add(wx.StaticText(panel, label="Context preview:"), flag=wx.LEFT | wx.TOP, border=8)
        self._preview = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self._preview.SetMinSize((-1, 100))
        vbox.Add(self._preview, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_refresh = wx.Button(panel, label="Refresh context")
        self._btn_send = wx.Button(panel, label="Approve && Send")
        self._btn_close = wx.Button(panel, label="Close")
        btn_row.Add(self._btn_refresh, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_send, flag=wx.RIGHT, border=6)
        btn_row.AddStretchSpacer()
        btn_row.Add(self._btn_close)
        vbox.Add(btn_row, flag=wx.EXPAND | wx.ALL, border=8)

        vbox.Add(wx.StaticText(panel, label="Response:"), flag=wx.LEFT, border=8)
        self._response = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self._response, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        self._status = wx.StaticText(panel, label="Collect context, review preview, then Approve & Send.")
        vbox.Add(self._status, flag=wx.ALL, border=8)

        panel.SetSizer(vbox)

        self._btn_refresh.Bind(wx.EVT_BUTTON, self._on_refresh)
        self._btn_send.Bind(wx.EVT_BUTTON, self._on_send)
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

        self._refresh_context()

    def _selected_template(self) -> str:
        labels = [
            "general_review",
            "pcb_layout_audit",
            "isolation_clearance_audit",
            "netlist_crosscheck",
            "netlist_gap_fill",
        ]
        idx = self._template_choice.GetSelection()
        if idx < 0 or idx >= len(labels):
            return "general_review"
        return labels[idx]

    def _context_flags(self) -> ContextIncludeFlags:
        return ContextIncludeFlags(
            schematic=self._chk_schematic.GetValue(),
            pcb=self._chk_pcb.GetValue(),
            bom=self._chk_bom.GetValue(),
            erc_drc=self._chk_erc_drc.GetValue(),
            netlist=self._chk_netlist.GetValue(),
        )

    def show_modal(self) -> int:
        return self._dialog.ShowModal()

    def _on_close(self, _event: wx.CommandEvent) -> None:
        self._dialog.EndModal(wx.ID_OK)

    def _on_refresh(self, _event: wx.CommandEvent) -> None:
        self._refresh_context()

    def _on_preview_update(self, _event: wx.CommandEvent) -> None:
        if self._ctx is not None:
            self._update_preview()

    def _refresh_context(self) -> None:
        self._status.SetLabel("Collecting context…")
        self._dialog.Layout()
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
        if self._approved:
            return
        question = self._txt_question.GetValue().strip()
        if not question:
            wx.MessageBox("Enter a question first.", "KiCad AI", wx.OK | wx.ICON_INFORMATION)
            return
        if self._ctx is None:
            self._refresh_context()
        if self._ctx is None:
            return

        if not wx.MessageBox(
            "Send this context and question to Anthropic?\n\n"
            "Review the preview above before approving.",
            "Approve transmission",
            wx.YES_NO | wx.ICON_QUESTION,
        ) == wx.YES:
            return

        self._approved = True
        self._btn_send.Enable(False)
        self._btn_refresh.Enable(False)

        built = build_chat_prompt(
            self._ctx,
            question,
            functional_description=self._txt_intent.GetValue().strip() or None,
            include_image=self._chk_image.GetValue(),
            include=self._context_flags(),
            template=self._selected_template(),
        )
        api_key = self._txt_key.GetValue().strip() or None
        approx_mb = (len(built.text) + built.image_byte_size) / (1024 * 1024)
        if built.include_image:
            self._status.SetLabel(
                f"Sending ~{approx_mb:.1f} MB (image + context) — "
                f"may take 2–6 min; read timeout {self._cfg.provider_read_timeout_sec}s…"
            )
        else:
            self._status.SetLabel("Sending to Claude…")
        self._dialog.Layout()

        threading.Thread(
            target=self._send_in_background,
            args=(built, api_key),
            daemon=True,
        ).start()

    def _send_in_background(self, built: BuiltPrompt, api_key: str | None) -> None:
        try:
            result = send_chat_prompt(
                built,
                self._ctx,  # type: ignore[arg-type]
                config=self._cfg,
                api_key_override=api_key,
            )
        except ProviderError as exc:
            wx.CallAfter(self._on_send_failed, exc)
            return
        wx.CallAfter(self._on_send_succeeded, result)

    def _on_send_failed(self, exc: ProviderError) -> None:
        self._approved = False
        self._btn_send.Enable(True)
        self._btn_refresh.Enable(True)
        self._status.SetLabel(f"Provider error: {exc}")
        wx.MessageBox(str(exc), "Provider error", wx.OK | wx.ICON_ERROR)

    def _on_send_succeeded(self, result: ChatSendResult) -> None:
        self._response.SetValue(result.response.text)
        self._btn_refresh.Enable(True)
        self._status.SetLabel(
            f"Done — {result.response.usage.input_tokens} in, "
            f"{result.response.usage.output_tokens} out tokens "
            f"({result.response.model})"
        )


def show_chat_dialog(
    project_path: Path | str,
    *,
    parent: wx.Window | None = None,
    retry_failed_urls: bool = False,
    force_refresh_urls: bool = False,
) -> None:
    """Show the KiCad AI chat dialog modally."""
    if wx is None:
        raise RuntimeError("wxPython is required; run inside KiCad or install wx on PYTHONPATH")
    path = Path(project_path).expanduser()
    dlg = ChatDialog(
        parent,
        path,
        retry_failed_urls=retry_failed_urls,
        force_refresh_urls=force_refresh_urls,
    )
    dlg.show_modal()
