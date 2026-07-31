"""AERF staged analysis panel (wxPython) with per-stage Approve & Send."""

from __future__ import annotations

import threading
from pathlib import Path

from context.model import ProjectContext
from prompts import BuiltPrompt
from providers.errors import ProviderError
from ui.aerf_supply import (
    build_aerf_stage_prompt_bundle,
    collect_aerf_context,
    send_aerf_stage_prompt,
)
from utils.config import load_config

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class AERFDialog:
    """Modal AERF dialog: stage-by-stage preview and Approve & Send."""

    def __init__(
        self,
        parent: wx.Window | None,
        project_path: Path,
        *,
        retry_failed_urls: bool = False,
        force_refresh_urls: bool = False,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for AERFDialog")
        self._project_path = project_path.expanduser().resolve()
        self._retry_failed_urls = retry_failed_urls
        self._force_refresh_urls = force_refresh_urls
        self._cfg = load_config()
        self._ctx: ProjectContext | None = None
        self._family_id = "blocking_oscillator"
        self._current_stage = 0
        self._completed_stages: list[dict] = []
        self._built: BuiltPrompt | None = None
        self._approved = False

        self._dialog = wx.Dialog(
            parent,
            title="AERF Staged Analysis",
            size=(820, 700),
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

        fam_row = wx.BoxSizer(wx.HORIZONTAL)
        fam_row.Add(wx.StaticText(panel, label="Circuit family:"), flag=wx.RIGHT, border=6)
        self._txt_family = wx.TextCtrl(panel, value=self._family_id)
        fam_row.Add(self._txt_family, proportion=1)
        vbox.Add(fam_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        stage_row = wx.BoxSizer(wx.HORIZONTAL)
        stage_row.Add(wx.StaticText(panel, label="AERF stage (0–7):"), flag=wx.RIGHT, border=6)
        self._spin_stage = wx.SpinCtrl(panel, min=0, max=7, initial=0)
        stage_row.Add(self._spin_stage, flag=wx.RIGHT, border=12)
        self._chk_image = wx.CheckBox(panel, label="Include schematic image")
        stage_row.Add(self._chk_image)
        stage_row.AddStretchSpacer()
        vbox.Add(stage_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        vbox.Add(wx.StaticText(panel, label="Context / prompt preview:"), flag=wx.LEFT | wx.TOP, border=8)
        self._preview = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self._preview.SetMinSize((-1, 160))
        vbox.Add(self._preview, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_refresh = wx.Button(panel, label="Refresh context")
        self._btn_preview = wx.Button(panel, label="Preview stage prompt")
        self._btn_send = wx.Button(panel, label="Approve && Send stage")
        self._btn_close = wx.Button(panel, label="Close")
        btn_row.Add(self._btn_refresh, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_preview, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_send, flag=wx.RIGHT, border=6)
        btn_row.AddStretchSpacer()
        btn_row.Add(self._btn_close)
        vbox.Add(btn_row, flag=wx.EXPAND | wx.ALL, border=8)

        vbox.Add(wx.StaticText(panel, label="Stage response:"), flag=wx.LEFT, border=8)
        self._response = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self._response, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        self._status = wx.StaticText(
            panel,
            label="Refresh context, preview each stage, then Approve & Send one stage at a time.",
        )
        vbox.Add(self._status, flag=wx.ALL, border=8)

        panel.SetSizer(vbox)

        self._btn_refresh.Bind(wx.EVT_BUTTON, self._on_refresh)
        self._btn_preview.Bind(wx.EVT_BUTTON, self._on_preview)
        self._btn_send.Bind(wx.EVT_BUTTON, self._on_send)
        self._btn_close.Bind(wx.EVT_BUTTON, self._on_close)
        self._spin_stage.Bind(wx.EVT_SPINCTRL, self._on_stage_change)

        self._refresh_context()

    def show_modal(self) -> int:
        return self._dialog.ShowModal()

    def _on_close(self, _event: wx.CommandEvent) -> None:
        self._dialog.EndModal(wx.ID_OK)

    def _on_stage_change(self, _event: wx.CommandEvent) -> None:
        self._current_stage = self._spin_stage.GetValue()

    def _on_refresh(self, _event: wx.CommandEvent) -> None:
        self._refresh_context()

    def _refresh_context(self) -> None:
        self._status.SetLabel("Collecting context…")
        self._dialog.Layout()
        try:
            self._ctx = collect_aerf_context(
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
        self._family_id = self._txt_family.GetValue().strip() or "blocking_oscillator"
        self._status.SetLabel(
            f"Context ready — {self._ctx.project_name}. Preview or send stage {self._current_stage}."
        )

    def _on_preview(self, _event: wx.CommandEvent) -> None:
        if self._ctx is None:
            self._refresh_context()
        if self._ctx is None:
            return
        self._current_stage = self._spin_stage.GetValue()
        self._family_id = self._txt_family.GetValue().strip() or "blocking_oscillator"
        plan, built = build_aerf_stage_prompt_bundle(
            self._ctx,
            self._family_id,
            self._current_stage,
            prior_stages=self._completed_stages,
            include_image=self._chk_image.GetValue(),
        )
        self._built = built
        preview_text = (
            f"{built.preview_summary}\n"
            f"KB: {plan.kb_excerpt_path}\n"
            f"Prior stages: {len(self._completed_stages)}\n"
            f"Estimated tokens: ~{built.estimated_text_tokens}\n"
            f"Template: {built.template}\n\n"
            "--- Prompt excerpt (first 1500 chars) ---\n"
            f"{built.text[:1500]}"
        )
        if len(built.text) > 1500:
            preview_text += "\n…"
        self._preview.SetValue(preview_text)
        self._status.SetLabel(f"Stage {self._current_stage} prompt ready — review, then Approve & Send.")

    def _on_send(self, _event: wx.CommandEvent) -> None:
        if self._approved:
            return
        if self._ctx is None:
            self._refresh_context()
        if self._ctx is None:
            return

        self._current_stage = self._spin_stage.GetValue()
        self._family_id = self._txt_family.GetValue().strip() or "blocking_oscillator"

        if not wx.MessageBox(
            f"Send AERF stage {self._current_stage} to the provider?\n\n"
            "Review the prompt preview before approving.",
            "Approve transmission",
            wx.YES_NO | wx.ICON_QUESTION,
        ) == wx.YES:
            return

        plan, built = build_aerf_stage_prompt_bundle(
            self._ctx,
            self._family_id,
            self._current_stage,
            prior_stages=self._completed_stages,
            include_image=self._chk_image.GetValue(),
        )
        self._built = built
        self._approved = True
        self._btn_send.Enable(False)
        self._status.SetLabel(f"Sending stage {self._current_stage}…")
        self._dialog.Layout()

        api_key = self._txt_key.GetValue().strip() or None
        threading.Thread(
            target=self._send_in_background,
            args=(built, plan.stage.stage_id, api_key),
            daemon=True,
        ).start()

    def _send_in_background(self, built: BuiltPrompt, stage_id: int, api_key: str | None) -> None:
        try:
            result = send_aerf_stage_prompt(
                built,
                self._ctx,  # type: ignore[arg-type]
                family_id=self._family_id,
                stage_id=stage_id,
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
        self._status.SetLabel(f"Provider error: {exc}")
        wx.MessageBox(str(exc), "Provider error", wx.OK | wx.ICON_ERROR)

    def _on_send_succeeded(self, result) -> None:
        self._approved = False
        self._btn_send.Enable(True)
        text = result.response.text
        if result.parse_error:
            text += f"\n\n--- Parse warning ---\n{result.parse_error}"
        elif result.parsed is not None:
            self._completed_stages.append(result.parsed)
            if self._current_stage < 7:
                self._current_stage += 1
                self._spin_stage.SetValue(self._current_stage)
        self._response.SetValue(text)
        self._status.SetLabel(
            f"Stage {result.stage_id} done — "
            f"{result.response.usage.input_tokens} in, "
            f"{result.response.usage.output_tokens} out tokens. "
            f"Completed stages: {len(self._completed_stages)}."
        )


def show_aerf_dialog(
    project_path: Path | str,
    *,
    parent: wx.Window | None = None,
    retry_failed_urls: bool = False,
    force_refresh_urls: bool = False,
) -> None:
    """Show the AERF staged analysis dialog modally."""
    if wx is None:
        raise RuntimeError("wxPython is required; run inside KiCad or install wx on PYTHONPATH")
    path = Path(project_path).expanduser()
    dlg = AERFDialog(
        parent,
        path,
        retry_failed_urls=retry_failed_urls,
        force_refresh_urls=force_refresh_urls,
    )
    dlg.show_modal()
