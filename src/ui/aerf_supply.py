"""Headless helpers for the AERF analysis UI.

Re-exports from ``inference.aerf`` for backward compatibility.
"""

from __future__ import annotations

from inference.aerf import (
    AERFPipelineResult,
    AERFStageRunResult,
    AERFSendResult,
    build_aerf_stage_prompt_bundle,
    build_stage0_bundle,
    parse_stage_output,
    run_aerf_pipeline,
    run_aerf_stage,
    send_aerf_stage_prompt,
)
from inference.chat import collect_chat_context as collect_aerf_context

__all__ = [
    "AERFPipelineResult",
    "AERFStageRunResult",
    "AERFSendResult",
    "build_aerf_stage_prompt_bundle",
    "build_stage0_bundle",
    "collect_aerf_context",
    "parse_stage_output",
    "run_aerf_pipeline",
    "run_aerf_stage",
    "send_aerf_stage_prompt",
]
