"""Tests for circuit family classifier."""

from __future__ import annotations

from context.model import ProjectContext
from context.schematic_parse import SymbolInstance
from reasoning.classifier import classify_circuit_family


def _blocking_oscillator_context() -> ProjectContext:
    return ProjectContext(
        project_path="/tmp/bo",
        project_name="blocking-demo",
        symbols=[
            SymbolInstance(
                reference="Q1",
                value="2N3055",
                lib_id="Device:Q_NPN_BCE",
            ),
            SymbolInstance(
                reference="T1",
                value="TriggerCoil",
                lib_id="Device:T_Core",
            ),
        ],
        schematic_connectivity={
            "unique_net_names": ["Trigger_Winding", "Coil_Plus", "GND"],
        },
    )


def test_classify_blocking_oscillator_heuristic() -> None:
    result = classify_circuit_family(_blocking_oscillator_context())
    assert result.family_id == "blocking_oscillator"
    assert result.confidence in ("medium", "high")
    assert any(b.startswith("symbol:") for b in result.recognition_basis)
    assert any(b.startswith("net:") for b in result.recognition_basis)


def test_classify_user_hint_override() -> None:
    ctx = ProjectContext(project_path="/tmp/p", project_name="empty")
    result = classify_circuit_family(ctx, user_hint="blocking oscillator")
    assert result.family_id == "blocking_oscillator"
    assert result.confidence == "high"
    assert "user_hint" in result.recognition_basis


def test_classify_low_confidence_empty_context() -> None:
    ctx = ProjectContext(project_path="/tmp/p", project_name="empty")
    result = classify_circuit_family(ctx)
    assert result.family_id == "generic"
    assert result.confidence == "low"


def test_classify_ekm_prior() -> None:
    ctx = ProjectContext(project_path="/tmp/p", project_name="empty")
    result = classify_circuit_family(ctx, ekm_family_id="blocking_oscillator")
    assert result.family_id == "blocking_oscillator"
    assert result.confidence in ("low", "medium")
    assert "ekm_prior" in result.recognition_basis
