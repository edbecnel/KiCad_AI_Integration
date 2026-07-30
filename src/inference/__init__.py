"""Engineering Inference Engine (EIE) — platform inference orchestration."""

from inference.aerf import AERFStage0Bundle, AERFStagePlan, build_stage0_bundle, plan_stage
from inference.chat import (
    ChatSendResult,
    build_chat_prompt,
    collect_chat_context,
    send_chat_prompt,
)
from inference.simulation import (
    GAP_LABELS,
    SimulationPanelContext,
    apply_simulation_model_for_part,
    apply_spice_fields_for_part,
    apply_spice_fields_from_catalog,
    get_simulation_panel_context,
    run_subckt_generation,
)

__all__ = [
    "AERFStage0Bundle",
    "AERFStagePlan",
    "ChatSendResult",
    "GAP_LABELS",
    "SimulationPanelContext",
    "apply_simulation_model_for_part",
    "apply_spice_fields_for_part",
    "apply_spice_fields_from_catalog",
    "build_chat_prompt",
    "build_stage0_bundle",
    "collect_chat_context",
    "get_simulation_panel_context",
    "plan_stage",
    "run_subckt_generation",
    "send_chat_prompt",
]
