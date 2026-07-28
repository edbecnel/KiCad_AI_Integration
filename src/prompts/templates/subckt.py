"""SUBCKT / .lib generation prompt templates (Tiers A, B, C)."""

from __future__ import annotations

import json
from typing import Any, Literal

SubcktTier = Literal["A", "B", "C"]

TIER_LABELS = {
    "A": "datasheet_backed",
    "B": "context_synthesized",
    "C": "inferred_last_resort",
}

SUBCKT_FACTS_SYSTEM = """You extract structured component facts from datasheet text for SPICE model generation.

Rules:
- Respond with JSON only.
- Do not invent specifications not supported by the provided text.
- List unknowns explicitly in "unknowns".
- Pin names and numbers must match the datasheet when present.
- Use the KiCad symbol pin list to align naming when the datasheet is ambiguous.

JSON schema:
{
  "part": "<part number>",
  "pinout": [{"pin": "1", "name": "...", "function": "..."}],
  "electrical_characteristics": [{"name": "...", "value": "...", "conditions": "..."}],
  "absolute_maximum_ratings": [{"name": "...", "value": "..."}],
  "behavior_notes": ["..."],
  "unknowns": ["..."],
  "confidence": "high|medium|low"
}"""


SUBCKT_SYNTHESIS_SYSTEM = """You generate ngspice-friendly SPICE .lib files with one .SUBCKT definition.

Rules:
- Respond with JSON only: {"subckt_name": "...", "lib_text": "...", "assumptions": ["..."], "abstraction": "datasheet_constrained|behavioral|placeholder"}
- lib_text must be valid ngspice-oriented syntax with .SUBCKT and .ENDS.
- Match .SUBCKT pin order to the KiCad symbol pin list exactly — not guessed datasheet order.
- Use behavioral/macro modeling unless the facts support a more detailed model.
- Never claim vendor-certified accuracy.
- Include comment lines documenting simplifications."""


SUBCKT_TIER_B_SYSTEM = """You synthesize an ngspice-friendly .lib SUBCKT from KiCad symbol and project context when no datasheet PDF is available.

Rules:
- Respond with JSON only: {"subckt_name": "...", "lib_text": "...", "assumptions": ["..."], "abstraction": "behavioral|placeholder", "limitations": ["..."], "unverified_parameters": ["..."]}
- Match .SUBCKT pin order to the KiCad symbol pin list exactly.
- List every assumption explicitly.
- abstraction must be behavioral or placeholder — not datasheet_backed."""


SUBCKT_TIER_C_SYSTEM = """You produce a last-resort draft ngspice .lib SUBCKT when datasheet and rich context are unavailable.

Rules:
- Respond with JSON only: {"subckt_name": "...", "lib_text": "...", "assumptions": ["..."], "abstraction": "placeholder", "limitations": ["..."], "unverified_parameters": ["..."]}
- Label output as draft only; use placeholder behavioral modeling.
- Match pin order to the KiCad symbol pin list when provided.
- Never imply datasheet-backed accuracy."""


def symbol_pin_context(symbol: dict[str, Any]) -> list[dict[str, str]]:
    pins: list[dict[str, str]] = []
    custom = symbol.get("custom_fields") or {}
    if isinstance(custom, dict):
        for key, value in sorted(custom.items()):
            if key.lower().startswith("pin") or "~" in key:
                pins.append({"field": str(key), "value": str(value)})
    return pins


def build_subckt_facts_prompt(
    part: str,
    symbol_context: dict[str, Any],
    *,
    datasheet_text: str,
    pdf_path: str | None = None,
) -> tuple[str, str]:
    """Tier A stage 1 — extract structured facts from datasheet text."""
    header = f"Part: {part}\n"
    if pdf_path:
        header += f"Datasheet path: {pdf_path}\n"
    user = (
        f"{header}\n"
        "KiCad symbol context:\n"
        f"{json.dumps(symbol_context, indent=2)}\n\n"
        "Datasheet text:\n"
        f"{datasheet_text}\n\n"
        "Return structured JSON facts only."
    )
    return user, SUBCKT_FACTS_SYSTEM


def build_subckt_synthesis_prompt(
    part: str,
    symbol_context: dict[str, Any],
    facts: dict[str, Any],
) -> tuple[str, str]:
    """Tier A stage 2 — synthesize .SUBCKT from extracted facts."""
    user = (
        f"Generate an ngspice .lib with one .SUBCKT for part {part}.\n\n"
        "Extracted datasheet facts:\n"
        f"{json.dumps(facts, indent=2)}\n\n"
        "KiCad symbol (match .SUBCKT pin order to this symbol):\n"
        f"{json.dumps(symbol_context, indent=2)}\n\n"
        'Return JSON only: {"subckt_name": "...", "lib_text": "...", "assumptions": [], "abstraction": "..."}'
    )
    return user, SUBCKT_SYNTHESIS_SYSTEM


def build_subckt_tier_b_prompt(
    part: str,
    symbol_context: dict[str, Any],
    *,
    project_context: dict[str, Any] | None = None,
) -> tuple[str, str]:
    user = (
        f"No datasheet PDF is available for {part}. "
        "Synthesize a draft behavioral SUBCKT from KiCad context.\n\n"
        f"Symbol:\n{json.dumps(symbol_context, indent=2)}\n"
    )
    if project_context:
        user += f"\nProject context:\n{json.dumps(project_context, indent=2)}\n"
    user += '\nReturn JSON only: {"subckt_name": "...", "lib_text": "...", ...}'
    return user, SUBCKT_TIER_B_SYSTEM


def build_subckt_tier_c_prompt(
    part: str,
    symbol_context: dict[str, Any],
) -> tuple[str, str]:
    user = (
        f"Last-resort draft SUBCKT for {part}. Thin context only.\n\n"
        f"Symbol:\n{json.dumps(symbol_context, indent=2)}\n\n"
        'Return JSON only with mandatory limitations and unverified_parameters.'
    )
    return user, SUBCKT_TIER_C_SYSTEM


def build_subckt_prompt_for_tier(
    tier: SubcktTier,
    part: str,
    symbol_context: dict[str, Any],
    *,
    datasheet_text: str = "",
    pdf_path: str | None = None,
    facts: dict[str, Any] | None = None,
    project_context: dict[str, Any] | None = None,
    stage: Literal["facts", "synthesis"] = "synthesis",
) -> tuple[str, str]:
    """Route to the appropriate SUBCKT prompt for a tier."""
    if tier == "A" and stage == "facts":
        return build_subckt_facts_prompt(
            part,
            symbol_context,
            datasheet_text=datasheet_text,
            pdf_path=pdf_path,
        )
    if tier == "A":
        return build_subckt_synthesis_prompt(
            part,
            symbol_context,
            facts or {"part": part, "unknowns": ["No facts extracted"]},
        )
    if tier == "B":
        return build_subckt_tier_b_prompt(
            part,
            symbol_context,
            project_context=project_context,
        )
    return build_subckt_tier_c_prompt(part, symbol_context)
