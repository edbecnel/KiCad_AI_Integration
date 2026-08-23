"""Engine-independent routing types (ADP-013)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

NetClassification = Literal[
    "critical_manual",
    "critical_constrained",
    "high_current",
    "power",
    "ground",
    "differential",
    "clock",
    "analog_sensitive",
    "rf",
    "sense",
    "ordinary_signal",
    "low_priority",
]


@dataclass
class BoardReference:
    """Host-neutral board identity."""

    project_path: Path
    pcb_path: Path | None = None
    checkpoint_path: Path | None = None

    def resolved_pcb_path(self) -> Path | None:
        if self.checkpoint_path and self.checkpoint_path.is_file():
            return self.checkpoint_path
        if self.pcb_path and self.pcb_path.is_file():
            return self.pcb_path
        candidate = self.project_path.parent / f"{self.project_path.stem}.kicad_pcb"
        return candidate if candidate.is_file() else self.pcb_path


@dataclass
class NetClassificationEntry:
    net_name: str
    classification: NetClassification
    explain: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "net_name": self.net_name,
            "classification": self.classification,
            "explain": self.explain,
        }


@dataclass
class RoutingPolicy:
    """Structured, engine-independent routing intent. Persisted per project."""

    net_classifications: list[NetClassificationEntry] = field(default_factory=list)
    notes: str = ""

    def excluded_nets(self) -> list[str]:
        excluded_classes = {
            "critical_manual",
            "critical_constrained",
            "high_current",
            "differential",
            "clock",
            "analog_sensitive",
            "rf",
            "sense",
        }
        return [
            entry.net_name
            for entry in self.net_classifications
            if entry.classification in excluded_classes
        ]

    def exclusion_explanations(self) -> dict[str, str]:
        return {
            entry.net_name: entry.explain
            for entry in self.net_classifications
            if entry.explain
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "net_classifications": [e.to_dict() for e in self.net_classifications],
            "notes": self.notes,
        }


@dataclass
class RoutingConstraints:
    """Width, clearance, and layer constraints (engine-independent)."""

    default_track_width_mm: float | None = None
    default_clearance_mm: float | None = None
    allowed_layers: list[str] = field(default_factory=list)
    net_width_overrides_mm: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "default_track_width_mm": self.default_track_width_mm,
            "default_clearance_mm": self.default_clearance_mm,
            "allowed_layers": self.allowed_layers,
            "net_width_overrides_mm": self.net_width_overrides_mm,
        }


@dataclass
class RoutingExclusions:
    """Nets and net-classes excluded from automatic routing."""

    excluded_nets: list[str] = field(default_factory=list)
    excluded_net_classes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "excluded_nets": self.excluded_nets,
            "excluded_net_classes": self.excluded_net_classes,
        }


@dataclass
class PreservedRoutes:
    """Existing routes that must not be overwritten."""

    preserved_net_names: list[str] = field(default_factory=list)
    preserve_all_existing: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "preserved_net_names": self.preserved_net_names,
            "preserve_all_existing": self.preserve_all_existing,
        }


@dataclass
class RoutingExecutionOptions:
    timeout_sec: int = 600
    batch_mode: bool = True
    working_directory: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "timeout_sec": self.timeout_sec,
            "batch_mode": self.batch_mode,
            "working_directory": str(self.working_directory) if self.working_directory else None,
        }


@dataclass
class RoutingRequest:
    board_reference: BoardReference
    routing_policy: RoutingPolicy = field(default_factory=RoutingPolicy)
    routing_constraints: RoutingConstraints = field(default_factory=RoutingConstraints)
    routing_exclusions: RoutingExclusions = field(default_factory=RoutingExclusions)
    preserved_routes: PreservedRoutes = field(default_factory=PreservedRoutes)
    execution_options: RoutingExecutionOptions = field(default_factory=RoutingExecutionOptions)


@dataclass
class ArtifactReference:
    """Reference to a routing artifact in the project exports directory."""

    path: Path
    kind: str
    label: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "path": str(self.path),
            "kind": self.kind,
            "label": self.label or self.kind,
        }


@dataclass
class RoutingProvenance:
    engine_id: str
    engine_version: str | None = None
    invocation_command: str | None = None
    started_at: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_version": self.engine_version,
            "invocation_command": self.invocation_command,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass
class RoutingResult:
    success: bool
    artifact_references: list[ArtifactReference] = field(default_factory=list)
    routed_net_count: int | None = None
    unrouted_net_count: int | None = None
    log_references: list[ArtifactReference] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    provenance: RoutingProvenance | None = None
    candidate_pcb_path: Path | None = None
    original_pcb_path: Path | None = None
    checkpoint_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "artifact_references": [a.to_dict() for a in self.artifact_references],
            "routed_net_count": self.routed_net_count,
            "unrouted_net_count": self.unrouted_net_count,
            "log_references": [a.to_dict() for a in self.log_references],
            "errors": self.errors,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "candidate_pcb_path": str(self.candidate_pcb_path) if self.candidate_pcb_path else None,
            "original_pcb_path": str(self.original_pcb_path) if self.original_pcb_path else None,
            "checkpoint_id": self.checkpoint_id,
        }


@dataclass
class RoutingEngineCapabilities:
    engine_id: str
    supports_automatic_routing: bool = False
    supports_batch_mode: bool = False
    supports_net_class_exclusions: bool = False
    supports_incremental_routing: bool = False
    supports_route_optimization: bool = False
    supports_progress_reporting: bool = False
    installed: bool = False
    version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "supports_automatic_routing": self.supports_automatic_routing,
            "supports_batch_mode": self.supports_batch_mode,
            "supports_net_class_exclusions": self.supports_net_class_exclusions,
            "supports_incremental_routing": self.supports_incremental_routing,
            "supports_route_optimization": self.supports_route_optimization,
            "supports_progress_reporting": self.supports_progress_reporting,
            "installed": self.installed,
            "version": self.version,
        }


@dataclass
class RoutingQualityReport:
    """Structured post-route quality metrics (Phase 4)."""

    routed_percentage: float | None = None
    via_count: int | None = None
    total_trace_length_mm: float | None = None
    layer_transition_count: int | None = None
    constraint_violations: list[str] = field(default_factory=list)
    critical_net_compliance: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "routed_percentage": self.routed_percentage,
            "via_count": self.via_count,
            "total_trace_length_mm": self.total_trace_length_mm,
            "layer_transition_count": self.layer_transition_count,
            "constraint_violations": self.constraint_violations,
            "critical_net_compliance": self.critical_net_compliance,
            "notes": self.notes,
        }
