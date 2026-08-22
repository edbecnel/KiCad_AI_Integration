"""Detect netlist connectivity gaps for AI-assisted gap-fill workflows."""

from __future__ import annotations

import re
from typing import Any

from context.schematic_parse import SymbolInstance

_AUTO_NET_RE = re.compile(r"^Net-\(", re.IGNORECASE)
_UNNAMED_NET_RE = re.compile(r"^unconnected-\(", re.IGNORECASE)


def is_auto_generated_net(name: str) -> bool:
    """True for KiCad auto net names like Net-(D1-Pad2)."""
    return bool(_AUTO_NET_RE.match(name.strip()))


def is_unconnected_net(name: str) -> bool:
    return bool(_UNNAMED_NET_RE.match(name.strip()))


def detect_connectivity_gaps(
    symbols: list[SymbolInstance],
    *,
    pin_connectivity: dict[str, Any] | None = None,
    connectivity_graph: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Flag symbols/pins with incomplete connectivity and auto-generated net names.

    Uses schematic pin lists plus optional SPICE netlist graph connections.
    """
    pin_data = pin_connectivity or {}
    symbol_pins: dict[str, list[dict[str, str]]] = pin_data.get("symbols") or {}

    connected: dict[str, set[str]] = {}
    if connectivity_graph:
        for entry in connectivity_graph.get("connections") or []:
            if not isinstance(entry, dict):
                continue
            ref = str(entry.get("reference") or "")
            pin = str(entry.get("pin") or "")
            net = str(entry.get("net") or "")
            if ref and pin and net:
                connected.setdefault(ref, set()).add(pin)

    auto_nets: list[str] = []
    if connectivity_graph:
        for net in connectivity_graph.get("nets") or []:
            name = str(net)
            if is_auto_generated_net(name) or is_unconnected_net(name):
                auto_nets.append(name)

    unconnected_pins: list[dict[str, str]] = []
    symbols_missing_pins: list[str] = []
    incomplete_symbols: list[str] = []

    for sym in symbols:
        if not sym.reference or sym.reference.startswith("#"):
            continue
        pins = symbol_pins.get(sym.reference) or []
        if not pins:
            symbols_missing_pins.append(sym.reference)
            continue
        resolved = connected.get(sym.reference, set())
        for pin_entry in pins:
            pin_num = pin_entry.get("pin", "")
            if pin_num and pin_num not in resolved:
                unconnected_pins.append(
                    {
                        "reference": sym.reference,
                        "pin": pin_num,
                        "sheet": sym.sheet_path,
                        "value": sym.value,
                    }
                )
        if resolved and len(resolved) < len(pins):
            incomplete_symbols.append(sym.reference)
        elif not resolved and pins:
            incomplete_symbols.append(sym.reference)

    return {
        "auto_generated_nets": sorted(set(auto_nets)),
        "unconnected_pins": unconnected_pins,
        "symbols_missing_pin_data": symbols_missing_pins,
        "incomplete_symbols": sorted(set(incomplete_symbols)),
        "gap_count": len(unconnected_pins) + len(auto_nets),
        "needs_connectivity_inference": bool(unconnected_pins or auto_nets),
    }
