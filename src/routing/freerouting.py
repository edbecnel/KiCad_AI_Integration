"""Freerouting routing engine provider (first reference implementation)."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from context.dsn_export import export_specctra_dsn
from context.routing_checkpoint import RoutingCheckpoint, create_routing_checkpoint
from context.ses_import import import_specctra_ses
from routing.errors import RoutingEngineError, RoutingSubprocessError, RoutingToolNotFoundError
from routing.types import (
    ArtifactReference,
    RoutingEngineCapabilities,
    RoutingProvenance,
    RoutingRequest,
    RoutingResult,
)
from utils.freerouting_cli import FreeroutingResolution, resolve_freerouting, try_resolve_freerouting

RunSubprocess = Callable[..., subprocess.CompletedProcess[str]]


@dataclass
class FreeroutingExchange:
    """Freerouting/Specctra-specific exchange (NOT in generic RoutingRequest)."""

    dsn_path: Path
    ses_output_path: Path
    excluded_net_classes: list[str]


class FreeroutingRoutingEngine:
    """First reference RoutingEngine implementation using Freerouting CLI + DSN/SES."""

    ENGINE_ID = "freerouting"

    def __init__(
        self,
        *,
        jar: str | None = None,
        cli: str | None = None,
        run_subprocess: RunSubprocess | None = None,
    ) -> None:
        self._jar = jar
        self._cli = cli
        self._run_subprocess = run_subprocess or subprocess.run
        self._resolution: FreeroutingResolution | None = None

    def _get_resolution(self) -> FreeroutingResolution:
        if self._resolution is None:
            self._resolution = resolve_freerouting(jar=self._jar, cli=self._cli)
        return self._resolution

    def capabilities(self) -> RoutingEngineCapabilities:
        resolution = try_resolve_freerouting(jar=self._jar, cli=self._cli)
        installed = resolution is not None and resolution.installed
        return RoutingEngineCapabilities(
            engine_id=self.ENGINE_ID,
            supports_automatic_routing=installed,
            supports_batch_mode=installed,
            supports_net_class_exclusions=installed,
            supports_incremental_routing=False,
            supports_route_optimization=installed,
            supports_progress_reporting=False,
            installed=installed,
            version=None,
        )

    def _translate_request(
        self,
        request: RoutingRequest,
        checkpoint: RoutingCheckpoint,
    ) -> FreeroutingExchange:
        exports = checkpoint.exports_dir
        dsn_path = exports / f"{checkpoint.checkpoint_id}.dsn"
        ses_path = exports / f"{checkpoint.checkpoint_id}.ses"
        excluded = list(request.routing_exclusions.excluded_net_classes)
        policy_excluded = request.routing_policy.excluded_nets()
        if policy_excluded:
            excluded.extend(policy_excluded)
        return FreeroutingExchange(
            dsn_path=dsn_path,
            ses_output_path=ses_path,
            excluded_net_classes=sorted(set(excluded)),
        )

    def route(self, request: RoutingRequest) -> RoutingResult:
        started_at = datetime.now(UTC).isoformat()
        pcb_path = request.board_reference.resolved_pcb_path()
        if pcb_path is None or not pcb_path.is_file():
            return RoutingResult(
                success=False,
                errors=[f"PCB not found for routing: {pcb_path}"],
            )

        try:
            resolution = self._get_resolution()
        except RoutingToolNotFoundError as exc:
            return RoutingResult(success=False, errors=[str(exc)])

        checkpoint = create_routing_checkpoint(pcb_path)
        exchange = self._translate_request(request, checkpoint)
        working_pcb = checkpoint.checkpoint_pcb_path

        dsn_result = export_specctra_dsn(working_pcb, exchange.dsn_path)
        if not dsn_result.success:
            return RoutingResult(
                success=False,
                errors=[dsn_result.message or "DSN export failed"],
                provenance=RoutingProvenance(engine_id=self.ENGINE_ID, started_at=started_at),
            )

        command = resolution.build_command(
            dsn_path=exchange.dsn_path,
            ses_path=exchange.ses_output_path,
            excluded_net_classes=exchange.excluded_net_classes,
        )

        cwd = request.execution_options.working_directory
        try:
            completed = self._run_subprocess(
                command,
                capture_output=True,
                text=True,
                timeout=request.execution_options.timeout_sec,
                cwd=str(cwd) if cwd else None,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RoutingSubprocessError(
                f"Freerouting timed out after {request.execution_options.timeout_sec}s"
            ) from exc

        log_path = checkpoint.exports_dir / f"{checkpoint.checkpoint_id}.freerouting.log"
        log_path.write_text(
            (completed.stdout or "") + "\n" + (completed.stderr or ""),
            encoding="utf-8",
        )

        if completed.returncode != 0:
            return RoutingResult(
                success=False,
                errors=[
                    f"Freerouting exited with code {completed.returncode}",
                    *(completed.stderr.splitlines()[-5:] if completed.stderr else []),
                ],
                log_references=[
                    ArtifactReference(path=log_path, kind="routing_log", label="Freerouting log")
                ],
                provenance=RoutingProvenance(
                    engine_id=self.ENGINE_ID,
                    invocation_command=" ".join(command),
                    started_at=started_at,
                    completed_at=datetime.now(UTC).isoformat(),
                ),
            )

        if not exchange.ses_output_path.is_file():
            return RoutingResult(
                success=False,
                errors=["Freerouting completed but SES file was not created."],
                log_references=[
                    ArtifactReference(path=log_path, kind="routing_log", label="Freerouting log")
                ],
            )

        candidate_path = checkpoint.candidate_pcb_path
        ses_result = import_specctra_ses(
            working_pcb,
            exchange.ses_output_path,
            output_path=candidate_path,
        )
        if not ses_result.success:
            return RoutingResult(
                success=False,
                errors=[ses_result.message or "SES import failed"],
                artifact_references=[
                    ArtifactReference(path=exchange.dsn_path, kind="dsn", label="Specctra DSN"),
                    ArtifactReference(path=exchange.ses_output_path, kind="ses", label="Specctra SES"),
                ],
                log_references=[
                    ArtifactReference(path=log_path, kind="routing_log", label="Freerouting log")
                ],
            )

        return RoutingResult(
            success=True,
            artifact_references=[
                ArtifactReference(path=exchange.dsn_path, kind="dsn", label="Specctra DSN"),
                ArtifactReference(path=exchange.ses_output_path, kind="ses", label="Specctra SES"),
                ArtifactReference(
                    path=checkpoint.checkpoint_pcb_path,
                    kind="checkpoint",
                    label="Board checkpoint",
                ),
            ],
            log_references=[
                ArtifactReference(path=log_path, kind="routing_log", label="Freerouting log")
            ],
            candidate_pcb_path=candidate_path,
            original_pcb_path=checkpoint.original_pcb_path,
            checkpoint_id=checkpoint.checkpoint_id,
            provenance=RoutingProvenance(
                engine_id=self.ENGINE_ID,
                invocation_command=" ".join(command),
                started_at=started_at,
                completed_at=datetime.now(UTC).isoformat(),
            ),
        )
