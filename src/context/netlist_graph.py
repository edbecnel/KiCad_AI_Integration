"""Parse SPICE netlist text into a compact connectivity graph for prompts."""

from __future__ import annotations

import re
from typing import Any

from context.simulation_gaps import parse_spice_netlist_includes

_AUTO_NET_RE = re.compile(r"^Net-\(", re.IGNORECASE)
_ELEMENT_PREFIXES = frozenset({"R", "C", "L", "D", "Q", "M", "X", "V", "I"})


def _is_element_line(parts: list[str]) -> bool:
    if not parts:
        return False
    ref = parts[0]
    if ref.startswith(".") or ref.startswith("*"):
        return False
    return ref[0].upper() in _ELEMENT_PREFIXES


def build_connectivity_graph(netlist_text: str) -> dict[str, Any] | None:
    """
    Build a compact graph from KiCad SPICE netlist export text.

    Returns None when the netlist is empty or has no parseable element lines.
    """
    if not netlist_text or not netlist_text.strip():
        return None

    connections: list[dict[str, str]] = []
    nets_set: set[str] = set()

    for raw_line in netlist_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith((".", "*")):
            continue
        parts = line.split()
        if not _is_element_line(parts):
            continue

        ref = parts[0]
        kind = ref[0].upper()

        if kind == "X" and len(parts) >= 4:
            subckt = parts[-1]
            net_nodes = parts[1:-1]
            for pin_idx, net in enumerate(net_nodes, start=1):
                nets_set.add(net)
                entry: dict[str, str] = {
                    "reference": ref,
                    "pin": str(pin_idx),
                    "net": net,
                }
                if subckt:
                    entry["subckt"] = subckt
                connections.append(entry)
        elif kind in ("R", "C", "L") and len(parts) >= 3:
            n1, n2 = parts[1], parts[2]
            nets_set.add(n1)
            nets_set.add(n2)
            connections.append({"reference": ref, "pin": "1", "net": n1})
            connections.append({"reference": ref, "pin": "2", "net": n2})
        elif kind in ("D", "Q", "M") and len(parts) >= 4:
            net_nodes = parts[1:-1]
            for pin_idx, net in enumerate(net_nodes, start=1):
                nets_set.add(net)
                connections.append({"reference": ref, "pin": str(pin_idx), "net": net})
        elif kind in ("V", "I") and len(parts) >= 3:
            n1, n2 = parts[1], parts[2]
            nets_set.add(n1)
            nets_set.add(n2)
            connections.append({"reference": ref, "pin": "+", "net": n1})
            connections.append({"reference": ref, "pin": "-", "net": n2})

    if not connections:
        return None

    nets = sorted(nets_set)
    auto_generated = sorted(n for n in nets if _AUTO_NET_RE.match(n))

    return {
        "nets": nets,
        "connections": connections,
        "connection_count": len(connections),
        "auto_generated_nets": auto_generated,
        "include_paths": parse_spice_netlist_includes(netlist_text),
    }


def build_connectivity_graph_from_summary(
    netlist_summary: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Build graph from ``ProjectContext.netlist_summary``."""
    if not netlist_summary:
        return None
    text = netlist_summary.get("text")
    if not isinstance(text, str):
        return None
    return build_connectivity_graph(text)
