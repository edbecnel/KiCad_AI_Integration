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
    *,
    ai_discovery_results: dict[str, object] | None = None,
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
        discovery = (ai_discovery_results or {}).get(part)
        if discovery is not None:
            entry["suggested_urls"] = list(getattr(discovery, "suggested_urls", []) or [])
            entry["discovery_outcome"] = getattr(discovery, "outcome", None)
            entry["discovery_error"] = getattr(discovery, "error", None)
            entry["selected_url"] = getattr(discovery, "selected_url", None)
        out.append(entry)
    return out


def summarize_required_datasheets(
    symbols: list[SymbolInstance],
    resolutions: dict[str, object],
    *,
    ai_discovery_results: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    """Group all datasheet-required symbols by Value (resolved and unresolved)."""
    grouped: dict[str, dict[str, object]] = {}
    status_rank = {"missing": 2, "fetch_failed": 1, "resolved": 0}

    for sym in symbols:
        res = resolutions.get(sym.reference)
        if res is None:
            continue
        requirement = classify_datasheet_requirement(sym)
        if requirement != "required":
            continue
        part = sym.value or sym.reference
        status = str(getattr(res, "status", "missing"))
        bucket = grouped.setdefault(
            part,
            {
                "part": part,
                "references": [],
                "status": status,
                "errors": set(),
                "artifact_id": None,
                "local_path": None,
                "sources_tried": set(),
            },
        )
        refs = bucket["references"]
        assert isinstance(refs, list)
        refs.append(sym.reference)
        current_status = str(bucket["status"])
        if status_rank.get(status, 0) > status_rank.get(current_status, 0):
            bucket["status"] = status
        for src in getattr(res, "sources_tried", []):
            tried = bucket["sources_tried"]
            assert isinstance(tried, set)
            tried.add(str(src))
            if str(src).startswith("fetch_error:"):
                errors = bucket["errors"]
                assert isinstance(errors, set)
                errors.add(str(src).replace("fetch_error:", "", 1))
        artifact_id = getattr(res, "artifact_id", None)
        if artifact_id and bucket["artifact_id"] is None:
            bucket["artifact_id"] = artifact_id
        local_path = getattr(res, "local_path", None)
        if local_path and bucket["local_path"] is None:
            bucket["local_path"] = str(local_path)

    out: list[dict[str, object]] = []
    for part in sorted(grouped):
        entry = grouped[part]
        errors = entry["errors"]
        assert isinstance(errors, set)
        entry["errors"] = sorted(errors)
        tried = entry["sources_tried"]
        assert isinstance(tried, set)
        entry["sources_tried"] = sorted(tried)
        refs = entry["references"]
        assert isinstance(refs, list)
        entry["reference_count"] = len(refs)
        entry["is_resolved"] = entry["status"] == "resolved"
        discovery = (ai_discovery_results or {}).get(part)
        if discovery is not None:
            entry["suggested_urls"] = list(getattr(discovery, "suggested_urls", []) or [])
            entry["discovery_outcome"] = getattr(discovery, "outcome", None)
            entry["discovery_error"] = getattr(discovery, "error", None)
            entry["selected_url"] = getattr(discovery, "selected_url", None)
        out.append(entry)
    return out


def format_required_datasheet_notice(
    symbols: list[SymbolInstance],
    resolutions: dict[str, object],
    *,
    library_path: Path | None = None,
    ai_discovery_results: dict[str, object] | None = None,
) -> str | None:
    """Human-readable notice when the user must supply PDFs manually."""
    missing = summarize_required_missing_datasheets(
        symbols,
        resolutions,
        ai_discovery_results=ai_discovery_results,
    )
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
        discovery_outcome = entry.get("discovery_outcome")
        discovery_error = entry.get("discovery_error")
        suggested = entry.get("suggested_urls") or []
        selected = entry.get("selected_url")
        symbol_url: str | None = None
        for sym in symbols:
            if (sym.value or sym.reference) == part and sym.datasheet.startswith("https://"):
                symbol_url = sym.datasheet
                break

        if discovery_outcome in ("fetch_failed", "no_url_found", "user_rejected"):
            err_text = discovery_error or (
                errors[0] if isinstance(errors, list) and errors else str(status)
            )
            lines.append(f"  {part} ({count} ref(s)): AI discovery failed — {err_text}")
        else:
            err_text = f" — {errors[0]}" if isinstance(errors, list) and errors else ""
            lines.append(f"  {part} ({count} ref(s)): {status}{err_text}")

        if symbol_url:
            lines.append(f"    Symbol URL: {symbol_url}")
        if selected and selected != symbol_url:
            lines.append(f"    Suggested URL: {selected}")
        elif suggested:
            for url in suggested[:3]:
                if url != symbol_url:
                    lines.append(f"    Suggested URL: {url}")
                    break
        safe_part = "".join(
            ch if ch.isalnum() or ch in "-_" else "_" for ch in str(part).strip()
        )
        manual_path = lib / "datasheets" / f"{safe_part or 'unknown_part'}.pdf"
        lines.append(
            f"    Manual: Attach PDF in Missing datasheets panel, or save as {manual_path}"
        )
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)
