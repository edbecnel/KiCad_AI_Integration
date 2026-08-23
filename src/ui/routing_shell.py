"""Embeddable Freerouting workflow panel (ADP-013 Phase 2)."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from context.model import ProjectContext
from inference.audit import AuditResult, run_post_route_review
from inference.routing import (
    RoutingPanelContext,
    accept_routing_result,
    build_routing_quality_report,
    build_routing_request,
    get_routing_panel_context,
    reject_routing_result,
    run_routing,
    run_routing_policy_generation,
)
from providers.errors import ProviderError
from routing.types import RoutingResult
from utils.config import AppConfig, load_config

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class RoutingShell(wx.Panel):
    """Intent-aware autorouting with checkpoint accept/reject and post-route review."""

    def __init__(
        self,
        parent: wx.Window,
        project_path: Path,
        *,
        embedded: bool = True,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for RoutingShell")
        super().__init__(parent)
        self._embedded = embedded
        self._project_path = project_path.expanduser().resolve()
        self._cfg = load_config()
        self._ctx: ProjectContext | None = None
        self._panel_ctx: RoutingPanelContext | None = None
        self._last_result: RoutingResult | None = None
        self._last_quality: dict[str, Any] | None = None
        self._busy = False

        vbox = wx.BoxSizer(wx.VERTICAL)
        intro = wx.StaticText(
            self,
            label=(
                "Run Freerouting autoroute with policy exclusions and checkpoint review. "
                "Requires routing_enabled, standalone Freerouting, and pcbnew for DSN/SES."
            ),
        )
        intro.Wrap(760)
        vbox.Add(intro, flag=wx.ALL, border=8)

        self._engine_info = wx.StaticText(self, label="Engine: —")
        vbox.Add(self._engine_info, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        policy_label = wx.StaticText(self, label="Routing policy / exclusions:")
        vbox.Add(policy_label, flag=wx.LEFT | wx.RIGHT, border=8)
        self._policy = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self._policy.SetMinSize((-1, 100))
        vbox.Add(self._policy, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=8)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_generate = wx.Button(self, label="Generate policy from AI")
        self._btn_run = wx.Button(self, label="Run autoroute")
        self._btn_accept = wx.Button(self, label="Accept candidate")
        self._btn_reject = wx.Button(self, label="Reject candidate")
        self._btn_review = wx.Button(self, label="Post-route AI review")
        self._btn_accept.Enable(False)
        self._btn_reject.Enable(False)
        self._btn_review.Enable(False)
        for btn in (
            self._btn_generate,
            self._btn_run,
            self._btn_accept,
            self._btn_reject,
            self._btn_review,
        ):
            btn_row.Add(btn, flag=wx.RIGHT, border=6)
        vbox.Add(btn_row, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        self._output = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self._output, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)

        self._status = wx.StaticText(self, label="Refresh project context to load routing panel.")
        vbox.Add(self._status, flag=wx.ALL, border=8)
        self.SetSizer(vbox)

        self._btn_generate.Bind(wx.EVT_BUTTON, self._on_generate_policy)
        self._btn_run.Bind(wx.EVT_BUTTON, self._on_run)
        self._btn_accept.Bind(wx.EVT_BUTTON, self._on_accept)
        self._btn_reject.Bind(wx.EVT_BUTTON, self._on_reject)
        self._btn_review.Bind(wx.EVT_BUTTON, self._on_post_route_review)

    def apply_context(self, ctx: ProjectContext) -> None:
        self._ctx = ctx
        self._panel_ctx = get_routing_panel_context(
            self._project_path,
            config=self._cfg,
        )
        self._last_result = None
        self._last_quality = None
        self._refresh_panel_state()
        self._output.SetValue("")
        self._status.SetLabel("Routing panel ready.")

    def _refresh_panel_state(self) -> None:
        panel = self._panel_ctx
        if panel is None:
            return

        caps = panel.capabilities
        engine_line = (
            f"Engine: {caps.engine_id} "
            f"({'installed' if caps.installed else 'not installed'})"
        )
        if caps.version:
            engine_line += f" v{caps.version}"
        self._engine_info.SetLabel(engine_line)

        lines: list[str] = []
        if panel.policy.notes:
            lines.append(panel.policy.notes)
        if panel.exclusion_explanations:
            lines.append("Exclusions:")
            lines.extend(f"  • {text}" for text in panel.exclusion_explanations)
        elif panel.policy.net_classifications:
            lines.append("No exclusion explanations configured.")
        else:
            lines.append("No net classifications in policy (all nets eligible).")
        self._policy.SetValue("\n".join(lines))

        can_run = (
            not self._busy
            and self._cfg.routing_enabled
            and panel.pcb_available
            and caps.installed
            and caps.supports_automatic_routing
        )
        self._btn_run.Enable(can_run)
        self._btn_generate.Enable(self._ctx is not None and not self._busy)

        has_candidate = (
            self._last_result is not None
            and self._last_result.success
            and self._last_result.candidate_pcb_path is not None
        )
        self._btn_accept.Enable(has_candidate and not self._busy)
        self._btn_reject.Enable(has_candidate and not self._busy)
        self._btn_review.Enable(
            has_candidate and not self._busy and self._ctx is not None
        )

        if not self._cfg.routing_enabled:
            self._status.SetLabel("Routing disabled — set routing_enabled=true in Settings.")
        elif not panel.pcb_available:
            self._status.SetLabel("No .kicad_pcb found for this project.")
        elif not caps.installed:
            self._status.SetLabel(
                "Freerouting not found — configure freerouting_jar or freerouting_cli."
            )

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._refresh_panel_state()

    def _on_generate_policy(self, _event: wx.CommandEvent) -> None:
        if self._busy or self._ctx is None:
            return
        if wx.MessageBox(
            "Send project context to the AI provider to generate a routing policy?",
            "Approve transmission",
            wx.YES_NO | wx.ICON_QUESTION,
        ) != wx.YES:
            return
        self._set_busy(True)
        self._status.SetLabel("Generating routing policy from AI…")
        threading.Thread(target=self._run_generate_policy_background, daemon=True).start()

    def _run_generate_policy_background(self) -> None:
        if self._ctx is None:
            wx.CallAfter(self._on_generate_policy_failed, "Project context not loaded.")
            return
        try:
            result = run_routing_policy_generation(self._ctx, config=self._cfg)
        except ProviderError as exc:
            wx.CallAfter(self._on_generate_policy_failed, str(exc))
            return
        except ValueError as exc:
            wx.CallAfter(self._on_generate_policy_failed, str(exc))
            return
        wx.CallAfter(self._on_generate_policy_succeeded, result)

    def _on_generate_policy_failed(self, message: str) -> None:
        self._set_busy(False)
        self._status.SetLabel(f"Policy generation failed: {message}")
        wx.MessageBox(message, "Policy generation error", wx.OK | wx.ICON_ERROR)

    def _on_generate_policy_succeeded(self, result) -> None:
        self._set_busy(False)
        self._panel_ctx = get_routing_panel_context(
            self._project_path,
            config=self._cfg,
            policy=result.policy,
        )
        self._refresh_panel_state()
        saved = result.saved_path
        saved_note = f" Saved: {saved}" if saved else ""
        self._status.SetLabel(
            f"Routing policy generated "
            f"({len(result.policy.net_classifications)} nets).{saved_note}"
        )

    def _on_run(self, _event: wx.CommandEvent) -> None:
        if self._busy or self._panel_ctx is None:
            return
        if wx.MessageBox(
            "Run Freerouting autoroute on a checkpoint copy of the board?",
            "Approve routing",
            wx.YES_NO | wx.ICON_QUESTION,
        ) != wx.YES:
            return
        self._set_busy(True)
        self._status.SetLabel("Routing in progress…")
        threading.Thread(target=self._run_route_background, daemon=True).start()

    def _run_route_background(self) -> None:
        panel = self._panel_ctx
        if panel is None:
            wx.CallAfter(self._on_route_failed, "Routing panel not initialized.")
            return
        request = build_routing_request(
            panel.project_path,
            policy=panel.policy,
            config=self._cfg,
        )
        try:
            result = run_routing(request, config=self._cfg)
        except Exception as exc:  # noqa: BLE001 — surface to UI
            wx.CallAfter(self._on_route_failed, str(exc))
            return
        if not result.success:
            message = "; ".join(result.errors) or "Routing failed."
            wx.CallAfter(self._on_route_failed, message, result)
            return
        quality = build_routing_quality_report(
            panel.project_path,
            result=result,
            config=self._cfg,
        )
        wx.CallAfter(self._on_route_succeeded, result, quality)

    def _format_result_summary(
        self,
        result: RoutingResult,
        quality: dict[str, Any] | None = None,
    ) -> str:
        lines = ["--- Routing result ---"]
        if result.routed_net_count is not None:
            lines.append(
                f"Routed nets: {result.routed_net_count}; "
                f"unrouted: {result.unrouted_net_count}"
            )
        if result.candidate_pcb_path:
            lines.append(f"Candidate PCB: {result.candidate_pcb_path}")
        for artifact in result.artifact_references:
            lines.append(f"Artifact ({artifact.kind}): {artifact.path}")
        if quality:
            lines.append("")
            lines.append("--- Quality report ---")
            if quality.get("routed_percentage") is not None:
                lines.append(f"Routed: {quality['routed_percentage']:.1f}%")
            if quality.get("via_count") is not None:
                lines.append(f"Vias: {quality['via_count']}")
            if quality.get("total_trace_length_mm") is not None:
                lines.append(
                    f"Total trace length: {quality['total_trace_length_mm']:.1f} mm"
                )
            for note in quality.get("notes") or []:
                lines.append(f"  {note}")
        return "\n".join(lines)

    def _on_route_failed(
        self,
        message: str,
        result: RoutingResult | None = None,
    ) -> None:
        self._set_busy(False)
        self._last_result = result
        self._last_quality = None
        if result is not None:
            self._output.SetValue(self._format_result_summary(result))
        self._status.SetLabel(f"Routing failed: {message}")
        wx.MessageBox(message, "Routing error", wx.OK | wx.ICON_ERROR)

    def _on_route_succeeded(self, result: RoutingResult, quality) -> None:
        self._set_busy(False)
        self._last_result = result
        self._last_quality = quality.to_dict()
        self._output.SetValue(self._format_result_summary(result, self._last_quality))
        self._status.SetLabel(
            "Routing complete — review candidate, then Accept or Reject."
        )
        self._refresh_panel_state()

    def _on_accept(self, _event: wx.CommandEvent) -> None:
        if self._last_result is None or self._busy:
            return
        if wx.MessageBox(
            "Promote the routing candidate to the authoritative board file?",
            "Accept routing",
            wx.YES_NO | wx.ICON_WARNING,
        ) != wx.YES:
            return
        try:
            path = accept_routing_result(self._last_result)
        except (ValueError, OSError) as exc:
            wx.MessageBox(str(exc), "Accept failed", wx.OK | wx.ICON_ERROR)
            return
        self._last_result = None
        self._last_quality = None
        self._refresh_panel_state()
        self._status.SetLabel(f"Accepted candidate — board updated: {path.name}")
        wx.MessageBox(
            f"Board updated:\n{path}\n\nReload the PCB in KiCad if it was open.",
            "Routing accepted",
            wx.OK | wx.ICON_INFORMATION,
        )

    def _on_reject(self, _event: wx.CommandEvent) -> None:
        if self._last_result is None or self._busy:
            return
        try:
            reject_routing_result(self._last_result)
        except (ValueError, OSError) as exc:
            wx.MessageBox(str(exc), "Reject failed", wx.OK | wx.ICON_ERROR)
            return
        self._last_result = None
        self._last_quality = None
        self._refresh_panel_state()
        self._status.SetLabel("Routing candidate discarded.")

    def _on_post_route_review(self, _event: wx.CommandEvent) -> None:
        if self._busy or self._ctx is None or self._last_result is None:
            return
        if wx.MessageBox(
            "Send post-route review to the configured AI provider?",
            "Approve transmission",
            wx.YES_NO | wx.ICON_QUESTION,
        ) != wx.YES:
            return
        self._set_busy(True)
        self._status.SetLabel("Running post-route AI review…")
        threading.Thread(target=self._run_review_background, daemon=True).start()

    def _run_review_background(self) -> None:
        if self._ctx is None or self._last_result is None:
            wx.CallAfter(self._on_review_failed, "No routing result to review.")
            return
        try:
            result = run_post_route_review(
                self._ctx,
                routing_result_summary=self._last_result.to_dict(),
                quality_report=self._last_quality,
                config=self._cfg,
            )
        except ProviderError as exc:
            wx.CallAfter(self._on_review_failed, str(exc))
            return
        wx.CallAfter(self._on_review_succeeded, result)

    def _on_review_failed(self, message: str) -> None:
        self._set_busy(False)
        self._status.SetLabel(f"Post-route review failed: {message}")
        wx.MessageBox(message, "Review error", wx.OK | wx.ICON_ERROR)

    def _on_review_succeeded(self, result: AuditResult) -> None:
        self._set_busy(False)
        lines = [self._output.GetValue(), "", "--- Post-route AI review ---", result.report.narrative]
        if result.report.findings:
            lines.append("")
            lines.append("--- Structured findings ---")
            for finding in result.report.findings:
                lines.append(
                    f"[{finding.severity}] {finding.category}: {finding.summary}"
                )
        self._output.SetValue("\n".join(lines).strip())
        saved = result.report_path
        saved_note = f" Saved: {saved}" if saved else ""
        self._status.SetLabel(
            f"Post-route review complete "
            f"({result.response.usage.input_tokens} in / "
            f"{result.response.usage.output_tokens} out).{saved_note}"
        )

    def confirm_close(self) -> bool:
        return not self._busy
