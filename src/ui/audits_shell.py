"""Embeddable one-click engineering audits panel (Phase 3)."""

from __future__ import annotations

import threading
from pathlib import Path

from context.model import ProjectContext
from inference.audit import (
    AuditResult,
    run_circuit_explanation,
    run_drc_interpretation,
    run_emi_emc_audit,
    run_flyback_recovery_audit,
    run_isolation_clearance_audit,
    run_pcb_layout_review,
    run_power_integrity_audit,
    run_schematic_review,
    run_signal_integrity_audit,
)
from providers.errors import ProviderError
from utils.config import load_config

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]

_AUDIT_RUNNERS = {
    "schematic": run_schematic_review,
    "pcb": run_pcb_layout_review,
    "drc": run_drc_interpretation,
    "isolation": run_isolation_clearance_audit,
    "circuit": run_circuit_explanation,
    "power_integrity": run_power_integrity_audit,
    "signal_integrity": run_signal_integrity_audit,
    "emi_emc": run_emi_emc_audit,
    "flyback": run_flyback_recovery_audit,
}


class AuditsShell(wx.Panel):
    """One-click schematic/PCB/domain audits with structured findings."""

    def __init__(
        self,
        parent: wx.Window,
        project_path: Path,
        *,
        embedded: bool = True,
    ) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for AuditsShell")
        super().__init__(parent)
        self._embedded = embedded
        self._project_path = project_path.expanduser().resolve()
        self._cfg = load_config()
        self._ctx: ProjectContext | None = None
        self._busy = False

        vbox = wx.BoxSizer(wx.VERTICAL)
        intro = wx.StaticText(
            self,
            label=(
                "Run structured engineering audits with one click. "
                "Reports are saved under kicad_ai/reviews/ after provider approval."
            ),
        )
        intro.Wrap(760)
        vbox.Add(intro, flag=wx.ALL, border=8)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_schematic = wx.Button(self, label="Schematic review")
        self._btn_pcb = wx.Button(self, label="PCB layout review")
        self._btn_drc = wx.Button(self, label="Explain DRC")
        self._btn_isolation = wx.Button(self, label="Isolation / clearance")
        self._btn_circuit = wx.Button(self, label="Circuit explanation")
        self._btn_power = wx.Button(self, label="Power integrity")
        self._btn_signal = wx.Button(self, label="Signal integrity")
        self._btn_emi = wx.Button(self, label="EMI / EMC")
        self._btn_flyback = wx.Button(self, label="Flyback recovery")
        for btn in (
            self._btn_schematic,
            self._btn_pcb,
            self._btn_drc,
            self._btn_isolation,
            self._btn_circuit,
            self._btn_power,
            self._btn_signal,
            self._btn_emi,
            self._btn_flyback,
        ):
            btn_row.Add(btn, flag=wx.RIGHT, border=6)
        vbox.Add(btn_row, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        self._findings = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self._findings, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)

        self._status = wx.StaticText(self, label="Refresh project context, then run an audit.")
        vbox.Add(self._status, flag=wx.ALL, border=8)
        self.SetSizer(vbox)

        self._btn_schematic.Bind(wx.EVT_BUTTON, lambda _e: self._start_audit("schematic"))
        self._btn_pcb.Bind(wx.EVT_BUTTON, lambda _e: self._start_audit("pcb"))
        self._btn_drc.Bind(wx.EVT_BUTTON, lambda _e: self._start_audit("drc"))
        self._btn_isolation.Bind(wx.EVT_BUTTON, lambda _e: self._start_audit("isolation"))
        self._btn_circuit.Bind(wx.EVT_BUTTON, lambda _e: self._start_audit("circuit"))
        self._btn_power.Bind(wx.EVT_BUTTON, lambda _e: self._start_audit("power_integrity"))
        self._btn_signal.Bind(wx.EVT_BUTTON, lambda _e: self._start_audit("signal_integrity"))
        self._btn_emi.Bind(wx.EVT_BUTTON, lambda _e: self._start_audit("emi_emc"))
        self._btn_flyback.Bind(wx.EVT_BUTTON, lambda _e: self._start_audit("flyback"))

    def apply_context(self, ctx: ProjectContext) -> None:
        self._ctx = ctx
        self._status.SetLabel("Context ready — choose an audit action.")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        for btn in (
            self._btn_schematic,
            self._btn_pcb,
            self._btn_drc,
            self._btn_isolation,
            self._btn_circuit,
            self._btn_power,
            self._btn_signal,
            self._btn_emi,
            self._btn_flyback,
        ):
            btn.Enable(not busy)

    def _start_audit(self, audit_key: str) -> None:
        if self._busy:
            return
        if self._ctx is None:
            wx.MessageBox("Refresh project context first.", "Audits", wx.OK | wx.ICON_INFORMATION)
            return
        if wx.MessageBox(
            "Send this audit request to the configured AI provider?",
            "Approve transmission",
            wx.YES_NO | wx.ICON_QUESTION,
        ) != wx.YES:
            return
        self._set_busy(True)
        self._status.SetLabel(f"Running {audit_key} audit…")
        threading.Thread(
            target=self._run_audit_background,
            args=(audit_key,),
            daemon=True,
        ).start()

    def _run_audit_background(self, audit_key: str) -> None:
        runner = _AUDIT_RUNNERS.get(audit_key)
        if runner is None or self._ctx is None:
            wx.CallAfter(self._on_audit_failed, "Unknown audit type.")
            return
        try:
            result = runner(self._ctx, config=self._cfg)
        except ProviderError as exc:
            wx.CallAfter(self._on_audit_failed, str(exc))
            return
        wx.CallAfter(self._on_audit_succeeded, result)

    def _on_audit_failed(self, message: str) -> None:
        self._set_busy(False)
        self._status.SetLabel(f"Audit failed: {message}")
        wx.MessageBox(message, "Audit error", wx.OK | wx.ICON_ERROR)

    def _on_audit_succeeded(self, result: AuditResult) -> None:
        self._set_busy(False)
        lines = [result.report.narrative, ""]
        if result.report.findings:
            lines.append("--- Structured findings ---")
            for finding in result.report.findings:
                lines.append(
                    f"[{finding.severity}] {finding.category}: {finding.summary} "
                    f"({', '.join(finding.references)})"
                )
        self._findings.SetValue("\n".join(lines).strip())
        saved = result.report_path
        saved_note = f" Saved: {saved}" if saved else ""
        self._status.SetLabel(
            f"{result.report.audit_type} — "
            f"{result.response.usage.input_tokens} in / "
            f"{result.response.usage.output_tokens} out tokens "
            f"({result.response.model}).{saved_note}"
        )

    def confirm_close(self) -> bool:
        return not self._busy
