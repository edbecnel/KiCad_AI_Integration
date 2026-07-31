"""Headless helpers for simulation / SUBCKT gap-fill UI.

Re-exports from ``inference.simulation`` for backward compatibility.
"""

from __future__ import annotations

from inference.simulation import (
    GAP_LABELS,
    SimulationPanelContext,
    apply_builtin_simulation_models_panel,
    apply_simulation_model_for_part,
    apply_spice_fields_for_part,
    apply_spice_fields_from_catalog,
    get_simulation_panel_context,
    run_subckt_generation,
)

__all__ = [
    "GAP_LABELS",
    "SimulationPanelContext",
    "apply_builtin_simulation_models_panel",
    "apply_simulation_model_for_part",
    "apply_spice_fields_for_part",
    "apply_spice_fields_from_catalog",
    "get_simulation_panel_context",
    "run_subckt_generation",
]
