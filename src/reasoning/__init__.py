"""AI Engineering Reasoning Framework (AERF) stage registry and KB loaders."""

from reasoning.classifier import (
    FamilyAlternative,
    FamilyClassification,
    classify_circuit_family,
)
from reasoning.family_registry import CircuitFamily, FamilyRecognition, get_family, load_families
from reasoning.kb_loader import KBExcerpt, KBLoadError, list_available_stage_files, load_stage_excerpt
from reasoning.stages import AERF_STAGE_COUNT, AERFStage, STAGES, get_stage, get_stage_by_key

__all__ = [
    "AERF_STAGE_COUNT",
    "AERFStage",
    "CircuitFamily",
    "FamilyAlternative",
    "FamilyClassification",
    "FamilyRecognition",
    "KBExcerpt",
    "KBLoadError",
    "STAGES",
    "classify_circuit_family",
    "get_family",
    "get_stage",
    "get_stage_by_key",
    "list_available_stage_files",
    "load_families",
    "load_stage_excerpt",
]
