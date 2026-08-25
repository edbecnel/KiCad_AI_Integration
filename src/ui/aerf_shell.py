"""Embeddable AERF staged analysis panel (wxPython) with per-stage Approve & Send."""

from __future__ import annotations

import threading
from pathlib import Path

from context.model import ProjectContext
from prompts import BuiltPrompt
from providers.errors import ProviderError
from ui.api_key_row import ApiKeyRow
from ui.aerf_supply import (
    build_aerf_stage_prompt_bundle,
    collect_aerf_context,
    plan_aerf_writeback,
    send_aerf_stage_prompt,
    write_aerf_stages_to_ekm,
)
from utils.config import load_config

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class AERFShell(wx.Panel):
    """Embeddable AERF panel: stage-by-stage preview and Approve & Send."""

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
            raise RuntimeError("wxPython is required for AERFShell")
        super().__init__(parent)
        self._embedded = embedded
        self._project_path = project_path.expanduser().resolve()
        self._retry_failed_urls = retry_failed_urls
        self._force_refresh_urls = force_refresh_urls
        self._cfg = load_config()
        self._ctx: ProjectContext | None = None
        self._family_id = "blocking_oscillator"
        self._current_stage = 0
        self._completed_stages: list[dict] = []
        self._ekm_sections: dict | None = None
        self._ekm_family_id: str | None = None
        self._built: BuiltPrompt | None = None
        self._approved = False
        self._last_sim_stage: dict | None = None
        self._last_sim_result = None
        vbox = wx.BoxSizer(wx.VERTICAL)

        api_key_row = ApiKeyRow.create(
            self,
            initial_value=self._cfg.anthropic_api_key,
        )
        self._api_key_row = api_key_row
        vbox.Add(api_key_row.sizer, flag=wx.EXPAND | wx.ALL, border=8)

        fam_row = wx.BoxSizer(wx.HORIZONTAL)
        fam_row.Add(wx.StaticText(self, label="Circuit family:"), flag=wx.RIGHT, border=6)
        self._txt_family = wx.TextCtrl(self, value=self._family_id)
        fam_row.Add(self._txt_family, proportion=1)
        vbox.Add(fam_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        stage_row = wx.BoxSizer(wx.HORIZONTAL)
        stage_row.Add(wx.StaticText(self, label="AERF stage (0–7):"), flag=wx.RIGHT, border=6)
        self._spin_stage = wx.SpinCtrl(self, min=0, max=7, initial=0)
        stage_row.Add(self._spin_stage, flag=wx.RIGHT, border=12)
        self._chk_image = wx.CheckBox(self, label="Include schematic image")
        stage_row.Add(self._chk_image)
        stage_row.AddStretchSpacer()
        vbox.Add(stage_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        vbox.Add(wx.StaticText(self, label="Context / prompt preview:"), flag=wx.LEFT | wx.TOP, border=8)
        self._preview = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self._preview.SetMinSize((-1, 160))
        vbox.Add(self._preview, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        if not self._embedded:
            self._btn_refresh = wx.Button(self, label="Refresh context")
            btn_row.Add(self._btn_refresh, flag=wx.RIGHT, border=6)
        self._btn_preview = wx.Button(self, label="Preview stage prompt")
        self._btn_send = wx.Button(self, label="Approve && Send stage")
        self._btn_writeback = wx.Button(self, label="Write to EKM…")
        self._btn_sim_plan = wx.Button(self, label="Run simulation plan")
        self._btn_merge_sim = wx.Button(self, label="Merge simulation refinement…")
        self._btn_writeback.Enable(False)
        self._btn_sim_plan.Enable(False)
        self._btn_merge_sim.Enable(False)
        btn_row.Add(self._btn_preview, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_send, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_writeback, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_sim_plan, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_merge_sim, flag=wx.RIGHT, border=6)
        btn_row.AddStretchSpacer()
        if not self._embedded:
            self._btn_close = wx.Button(self, label="Close")
            btn_row.Add(self._btn_close)
        vbox.Add(btn_row, flag=wx.EXPAND | wx.ALL, border=8)

        vbox.Add(wx.StaticText(self, label="Stage response:"), flag=wx.LEFT, border=8)
        self._response = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self._response, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        self._status = wx.StaticText(
            self,
            label="Refresh context, preview each stage, then Approve & Send one stage at a time.",
        )
        vbox.Add(self._status, flag=wx.ALL, border=8)

        self.SetSizer(vbox)

        if not self._embedded:
            self._btn_refresh.Bind(wx.EVT_BUTTON, self._on_refresh)
        self._btn_preview.Bind(wx.EVT_BUTTON, self._on_preview)
        self._btn_send.Bind(wx.EVT_BUTTON, self._on_send)
        self._btn_writeback.Bind(wx.EVT_BUTTON, self._on_writeback)
        self._btn_sim_plan.Bind(wx.EVT_BUTTON, self._on_run_simulation_plan)
        self._btn_merge_sim.Bind(wx.EVT_BUTTON, self._on_merge_simulation_refinement)
        if not self._embedded:
            self._btn_close.Bind(wx.EVT_BUTTON, self._on_close)
        self._spin_stage.Bind(wx.EVT_SPINCTRL, self._on_stage_change)

        if not self._embedded:
            self._refresh_context()

    def apply_context(self, ctx: ProjectContext) -> None:
        """Use project context from the Assistant shell header."""
        from ekm.prompt_context import load_ekm_prompt_bundle

        self._ctx = ctx
        bundle = load_ekm_prompt_bundle(self._project_path)
        self._ekm_sections = bundle.sections or None
        self._ekm_family_id = bundle.family_id
        if self._ekm_family_id and not self._txt_family.GetValue().strip():
            self._txt_family.SetValue(self._ekm_family_id)
        self._family_id = self._txt_family.GetValue().strip() or "blocking_oscillator"
        ekm_note = "EKM loaded" if self._ekm_sections else "no EKM"
        self._status.SetLabel(
            f"Context ready — {ctx.project_name} ({ekm_note}). "
            f"Preview or send stage {self._current_stage}."
        )

    def confirm_close(self) -> bool:
        return True

    def _on_close(self, _event: wx.CommandEvent) -> None:
        top = self.GetTopLevelParent()
        if hasattr(top, "EndModal"):
            top.EndModal(wx.ID_OK)

    def _on_stage_change(self, _event: wx.CommandEvent) -> None:
        self._current_stage = self._spin_stage.GetValue()

    def _on_refresh(self, _event: wx.CommandEvent) -> None:
        if not self._embedded:
            self._refresh_context()

    def _refresh_context(self) -> None:
        self._status.SetLabel("Collecting context…")
        self.Layout()
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
        from ekm.prompt_context import load_ekm_prompt_bundle

        bundle = load_ekm_prompt_bundle(self._project_path)
        self._ekm_sections = bundle.sections or None
        self._ekm_family_id = bundle.family_id
        if self._ekm_family_id and not self._txt_family.GetValue().strip():
            self._txt_family.SetValue(self._ekm_family_id)
        self._family_id = self._txt_family.GetValue().strip() or "blocking_oscillator"
        ekm_note = "EKM loaded" if self._ekm_sections else "no EKM"
        self._status.SetLabel(
            f"Context ready — {self._ctx.project_name} ({ekm_note}). "
            f"Preview or send stage {self._current_stage}."
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
            ekm_sections=self._ekm_sections,
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

    def _update_writeback_button(self) -> None:
        has_stage_7 = any(
            isinstance(stage.get("stage_id"), int) and stage["stage_id"] == 7
            for stage in self._completed_stages
        )
        self._btn_writeback.Enable(has_stage_7)

    def _on_writeback(self, _event: wx.CommandEvent) -> None:
        if not self._completed_stages:
            return

        plan = plan_aerf_writeback(self._completed_stages)
        preview_lines = [plan.summary]
        for field_plan in plan.field_plans[:12]:
            preview_lines.append(
                f"• {field_plan.section_id}/{field_plan.field_id}: {field_plan.value_preview}"
            )
        if len(plan.field_plans) > 12:
            preview_lines.append(f"… and {len(plan.field_plans) - 12} more field(s)")

        if not wx.MessageBox(
            "Write approved AERF conclusions to Engineering Knowledge?\n\n"
            + "\n".join(preview_lines),
            "Approve EKM write-back",
            wx.YES_NO | wx.ICON_QUESTION,
        ) == wx.YES:
            return

        try:
            _plan, saved = write_aerf_stages_to_ekm(
                self._project_path,
                self._completed_stages,
                approve=True,
            )
        except OSError as exc:
            wx.MessageBox(str(exc), "EKM write-back error", wx.OK | wx.ICON_ERROR)
            return

        promo_msg = ""
        try:
            from learning.family_promotion import try_auto_promote

            promo = try_auto_promote(
                self._completed_stages,
                self._ctx,  # type: ignore[arg-type]
                self._project_path,
                config=self._cfg,
            )
            if promo.promoted:
                promo_msg = f"\nPromoted to library family: {promo.family_id}"
            elif promo.message != "auto_promote_disabled":
                promo_msg = f"\nLibrary promotion skipped: {promo.message}"
        except OSError as exc:
            promo_msg = f"\nLibrary promotion error: {exc}"

        self._status.SetLabel(f"EKM updated — {saved}")
        wx.MessageBox(
            f"Engineering knowledge saved to:\n{saved}{promo_msg}",
            "EKM write-back",
            wx.OK | wx.ICON_INFORMATION,
        )

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
            ekm_sections=self._ekm_sections,
            include_image=self._chk_image.GetValue(),
        )
        self._built = built
        self._approved = True
        self._btn_send.Enable(False)
        self._status.SetLabel(f"Sending stage {self._current_stage}…")
        self.Layout()

        api_key = self._api_key_row.get_value().strip() or None
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
        self._update_writeback_button()
        self._update_sim_plan_button()

    def _latest_stage_with_hooks(self) -> dict | None:
        for stage in reversed(self._completed_stages):
            hooks = stage.get("simulation_hooks")
            if isinstance(hooks, list) and hooks:
                return stage
        return None

    def _update_sim_plan_button(self) -> None:
        self._btn_sim_plan.Enable(self._latest_stage_with_hooks() is not None)

    def _on_run_simulation_plan(self, _event: wx.CommandEvent) -> None:
        stage = self._latest_stage_with_hooks()
        if stage is None:
            wx.MessageBox(
                "No completed stage with simulation_hooks found.",
                "Simulation plan",
                wx.OK | wx.ICON_INFORMATION,
            )
            return
        if wx.MessageBox(
            "Run closed-loop simulation plan for the latest stage with hooks?",
            "Approve simulation",
            wx.YES_NO | wx.ICON_QUESTION,
        ) != wx.YES:
            return
        self._btn_sim_plan.Enable(False)
        self._status.SetLabel("Running simulation plan…")
        threading.Thread(
            target=self._run_simulation_plan_background,
            args=(stage,),
            daemon=True,
        ).start()

    def _run_simulation_plan_background(self, stage: dict) -> None:
        from inference.simulation_closed_loop import translate_simulation_hooks
        from inference.simulation_runner import run_simulation_plan

        plan = translate_simulation_hooks(stage)
        if plan is None:
            wx.CallAfter(
                self._on_simulation_plan_failed,
                "Could not translate simulation hooks.",
            )
            return
        result = run_simulation_plan(self._project_path, plan, config=self._cfg)
        wx.CallAfter(self._on_simulation_plan_succeeded, result)

    def _on_simulation_plan_failed(self, message: str) -> None:
        self._update_sim_plan_button()
        self._status.SetLabel(f"Simulation plan failed: {message}")
        wx.MessageBox(message, "Simulation plan", wx.OK | wx.ICON_ERROR)

    def _on_simulation_plan_succeeded(self, result) -> None:
        self._last_sim_stage = self._latest_stage_with_hooks()
        self._last_sim_result = result
        self._update_sim_plan_button()
        self._btn_merge_sim.Enable(self._last_sim_stage is not None and result is not None)
        lines = [
            self._response.GetValue(),
            "",
            "--- Simulation plan result ---",
            f"Success: {result.success}",
        ]
        for measurement in result.measurements:
            lines.append(f"  {measurement.name}: {measurement.value}")
        for ref in getattr(result, "artifact_references", []) or []:
            lines.append(f"  Artifact: {ref.get('id')} → {ref.get('path')}")
        for err in result.errors:
            lines.append(f"  Error: {err}")
        if result.log_excerpt:
            lines.append(result.log_excerpt[-500:])
        self._response.SetValue("\n".join(lines).strip())
        self._status.SetLabel(
            "Simulation plan complete — review results, then Merge simulation refinement if approved."
        )

    def _on_merge_simulation_refinement(self, _event: wx.CommandEvent) -> None:
        if self._last_sim_stage is None or self._last_sim_result is None:
            wx.MessageBox(
                "Run a simulation plan first.",
                "Merge refinement",
                wx.OK | wx.ICON_INFORMATION,
            )
            return
        if wx.MessageBox(
            "Merge simulation measurements into the stage determinations?",
            "Approve refinement merge",
            wx.YES_NO | wx.ICON_QUESTION,
        ) != wx.YES:
            return
        from inference.simulation_closed_loop import (
            build_refinement_from_simulation,
            merge_refinement_into_stage,
        )

        refinement = build_refinement_from_simulation(
            self._last_sim_stage,
            self._last_sim_result,
            approved=True,
        )
        merged = merge_refinement_into_stage(self._last_sim_stage, refinement)
        stage_id = merged.get("stage_id")
        replaced = False
        for index, stage in enumerate(self._completed_stages):
            if stage.get("stage_id") == stage_id:
                self._completed_stages[index] = merged
                replaced = True
                break
        if not replaced:
            self._completed_stages.append(merged)
        self._response.SetValue(
            "\n".join(
                [
                    self._response.GetValue(),
                    "",
                    "--- Merged simulation refinement ---",
                    f"Stage {stage_id}: simulation_validation written to determinations.",
                ]
            ).strip()
        )
        self._status.SetLabel("Simulation refinement merged — use Write to EKM to persist.")
        self._update_writeback_button()

