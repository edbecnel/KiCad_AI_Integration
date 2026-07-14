"""Heuristics for when a schematic symbol needs a datasheet PDF."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from context.schematic_parse import SymbolInstance

DatasheetRequirement = Literal["required", "optional", "not_applicable"]

# Reference prefixes that never need datasheets for netlist/SUBCKT gap-fill.
_NOT_APPLICABLE_REF_PREFIXES = ("#",)

# lib_id prefixes treated as passives / structural (no PDF for netlist analysis).
_PASSIVE_LIB_PREFIXES = (
    "device:r",
    "device:c",
    "device:l",
    "device:ferrite",
    "device:fuse",
    "device:led",
    "device:d",
    "jumper:",
    "connector:testpoint",
    "connector:conn_",
    "connector:screw_terminal",
    "power:",
)

# lib_id / value hints for active or specialized parts (PDF required for SUBCKT).
_REQUIRED_LIB_FRAGMENTS = (
    "transistor",
    "fet",
    "mosfet",
    "scr",
    "triac",
    "thyristor",
    "converter",
    "regulator",
    "opamp",
    "amplifier",
    "driver",
    "optocoupler",
    "optocoupl",
    "gate_driver",
    "sensor",
    "mcu",
    "processor",
    "fpga",
    "memory",
    "adc",
    "dac",
    "pmic",
)

_STANDARD_DIODE_VALUES = re.compile(
    r"^(1N4148|1N400[1-7]|1N5819|BZX84|MM3Z|PDZ|SS1[0-9]|BAT54)",
    re.I,
)


def classify_datasheet_requirement(symbol: SymbolInstance) -> DatasheetRequirement:
    """Classify whether a symbol typically needs a user-supplied datasheet PDF."""
    ref = symbol.reference.strip().upper()
    if not ref or ref.startswith(_NOT_APPLICABLE_REF_PREFIXES):
        return "not_applicable"

    lib_id = (symbol.lib_id or "").lower()
    value = (symbol.value or "").strip()
    value_upper = value.upper()

    if not value or value_upper in ("GND", "GNDREF", "VCC", "VDD", "VSS"):
        return "not_applicable"

    if lib_id.startswith("power:"):
        return "not_applicable"

    if lib_id.startswith(_PASSIVE_LIB_PREFIXES):
        if lib_id.startswith("device:d") and not _STANDARD_DIODE_VALUES.match(value):
            return "required"
        if lib_id.startswith("device:led"):
            return "optional"
        return "optional" if lib_id.startswith(("device:r", "device:c", "device:l")) else "not_applicable"

    if any(frag in lib_id for frag in _REQUIRED_LIB_FRAGMENTS):
        return "required"

    if ref.startswith("U"):
        return "required"

    if ref.startswith(("Q", "SCR")):
        return "required"

    if ref.startswith("D"):
        if _STANDARD_DIODE_VALUES.match(value):
            return "optional"
        return "required"

    if ref.startswith(("R", "C", "L", "F", "FB", "TP", "J", "JP")):
        return "optional"

    if symbol.footprint or symbol.custom_fields:
        return "required"

    if value:
        return "optional"

    return "not_applicable"


def needs_user_pdf(resolution_status: str, requirement: DatasheetRequirement) -> bool:
    """True when the user should be prompted to supply a PDF manually."""
    if requirement != "required":
        return False
    return resolution_status in ("fetch_failed", "missing")


def summarize_required_missing_datasheets(
    symbols: list[SymbolInstance],
    resolutions: dict[str, object],
) -> list[dict[str, object]]:
    """Group datasheet-required symbols that still lack a resolved PDF."""
    grouped: dict[str, dict[str, object]] = {}
    for sym in symbols:
        res = resolutions.get(sym.reference)
        if res is None:
            continue
        status = getattr(res, "status", "missing")
        requirement = classify_datasheet_requirement(sym)
        if not needs_user_pdf(str(status), requirement):
            continue
        part = sym.value or sym.reference
        bucket = grouped.setdefault(
            part,
            {
                "part": part,
                "references": [],
                "status": status,
                "errors": set(),
            },
        )
        refs = bucket["references"]
        assert isinstance(refs, list)
        refs.append(sym.reference)
        for src in getattr(res, "sources_tried", []):
            if str(src).startswith("fetch_error:"):
                errors = bucket["errors"]
                assert isinstance(errors, set)
                errors.add(str(src).replace("fetch_error:", "", 1))
    out: list[dict[str, object]] = []
    for part in sorted(grouped):
        entry = grouped[part]
        errors = entry["errors"]
        assert isinstance(errors, set)
        entry["errors"] = sorted(errors)
        refs = entry["references"]
        assert isinstance(refs, list)
        entry["reference_count"] = len(refs)
        out.append(entry)
    return out


def format_required_datasheet_notice(
    symbols: list[SymbolInstance],
    resolutions: dict[str, object],
    *,
    library_path: Path | None = None,
) -> str | None:
    """Human-readable notice when the user must supply PDFs manually."""
    missing = summarize_required_missing_datasheets(symbols, resolutions)
    if not missing:
        return None
    lib = library_path.expanduser() if library_path else Path("~/kicad_ai_library")
    lines = [
        "--- Manual datasheets required (auto-fetch failed or missing) ---",
        "PDFs are required for SUBCKT generation and detailed analysis of these parts.",
        "",
    ]
    for entry in missing:
        part = entry["part"]
        count = entry["reference_count"]
        status = entry["status"]
        errors = entry["errors"]
        err_text = f" — {errors[0]}" if isinstance(errors, list) and errors else ""
        lines.append(f"  {part} ({count} ref(s)): {status}{err_text}")
    lines.extend(
        [
            "",
            f"Supply PDFs: save as {lib}/datasheets/<Value>.pdf and re-run,",
            "or use the planned drag-and-drop UI (see docs/Specifications/Datasheet_Requirements_and_User_Supply.md).",
        ]
    )
    return "\n".join(lines)
