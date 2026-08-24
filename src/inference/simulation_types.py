"""Host-neutral simulation closed-loop types and translation (ADP-006)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

SimulationAnalysisKind = Literal["transient", "dc", "ac", "parametric", "unknown"]


@dataclass
class SimulationHook:
    """One AERF ``simulation_hooks`` entry from a stage envelope."""

    description: str
    validates: str = ""
    expected_outcome: str = ""
    analysis_kind: SimulationAnalysisKind = "unknown"
    probes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "validates": self.validates,
            "expected_outcome": self.expected_outcome,
            "analysis_kind": self.analysis_kind,
            "probes": self.probes,
        }


@dataclass
class SimulationPlanStep:
    """Executable simulation step derived from hooks."""

    hook: SimulationHook
    netlist_required: bool = True
    subckt_parts: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hook": self.hook.to_dict(),
            "netlist_required": self.netlist_required,
            "subckt_parts": self.subckt_parts,
            "notes": self.notes,
        }


@dataclass
class SimulationPlan:
    """Host-neutral plan produced from AERF simulation hooks."""

    stage_id: int | None
    stage_key: str
    steps: list[SimulationPlanStep] = field(default_factory=list)
    source_hooks: list[SimulationHook] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "stage_key": self.stage_key,
            "steps": [step.to_dict() for step in self.steps],
            "source_hooks": [hook.to_dict() for hook in self.source_hooks],
        }


@dataclass
class SimulationMeasurement:
    """Normalized measurement from a host solver."""

    name: str
    value: float | str | None = None
    unit: str = ""
    passed: bool | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "passed": self.passed,
            "notes": self.notes,
        }


@dataclass
class SimulationResult:
    """Host-neutral simulation outcome for closed-loop refinement."""

    plan: SimulationPlan
    success: bool
    measurements: list[SimulationMeasurement] = field(default_factory=list)
    waveform_paths: list[str] = field(default_factory=list)
    artifact_references: list[dict[str, str]] = field(default_factory=list)
    log_excerpt: str = ""
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan.to_dict(),
            "success": self.success,
            "measurements": [m.to_dict() for m in self.measurements],
            "waveform_paths": self.waveform_paths,
            "artifact_references": self.artifact_references,
            "log_excerpt": self.log_excerpt,
            "errors": self.errors,
        }


@dataclass
class StageRefinement:
    """User-approved refinement to prior stage determinations."""

    stage_id: int
    stage_key: str
    validated_determinations: dict[str, Any] = field(default_factory=dict)
    challenged_determinations: dict[str, Any] = field(default_factory=dict)
    refinement_notes: list[str] = field(default_factory=list)
    artifact_references: list[dict[str, str]] = field(default_factory=list)
    approved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "stage_key": self.stage_key,
            "validated_determinations": self.validated_determinations,
            "challenged_determinations": self.challenged_determinations,
            "refinement_notes": self.refinement_notes,
            "artifact_references": self.artifact_references,
            "approved": self.approved,
        }
