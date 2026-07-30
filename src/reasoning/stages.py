"""Canonical AERF stage registry (stages 0–7)."""

from __future__ import annotations

from dataclasses import dataclass

AERF_STAGE_COUNT = 8

# Default stage file title suffixes (match Circuit_Families file naming)
STAGE_FILE_TITLES: tuple[str, ...] = (
    "Circuit Identification",
    "Basic Oscillation",
    "Energy Flow",
    "Physical Principles",
    "Component Roles",
    "Operating Modes",
    "System Behavior",
    "Engineering Analysis",
)


@dataclass(frozen=True)
class AERFStage:
    stage_id: int
    stage_key: str
    title: str
    file_title: str

    @property
    def filename(self) -> str:
        return f"{self.stage_id:02d} - {self.file_title}.md"


# stage_key from AERF_Stage_Index.md; titles 1–6 overridable per family
STAGES: tuple[AERFStage, ...] = (
    AERFStage(0, "circuit_identification", "Circuit Identification", STAGE_FILE_TITLES[0]),
    AERFStage(1, "basic_operation", "Basic Operation", STAGE_FILE_TITLES[1]),
    AERFStage(2, "energy_flow", "Energy Flow", STAGE_FILE_TITLES[2]),
    AERFStage(3, "physical_principles", "Physical Principles", STAGE_FILE_TITLES[3]),
    AERFStage(4, "component_roles", "Component Roles", STAGE_FILE_TITLES[4]),
    AERFStage(5, "operating_modes", "Operating Modes", STAGE_FILE_TITLES[5]),
    AERFStage(6, "system_behavior", "System Behavior", STAGE_FILE_TITLES[6]),
    AERFStage(7, "engineering_analysis", "Engineering Analysis", STAGE_FILE_TITLES[7]),
)


def get_stage(stage_id: int) -> AERFStage:
    for stage in STAGES:
        if stage.stage_id == stage_id:
            return stage
    raise KeyError(f"Unknown AERF stage_id: {stage_id}")


def get_stage_by_key(stage_key: str) -> AERFStage:
    for stage in STAGES:
        if stage.stage_key == stage_key:
            return stage
    raise KeyError(f"Unknown AERF stage_key: {stage_key}")
