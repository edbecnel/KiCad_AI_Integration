"""Extract net labels and schematic connectivity from .kicad_sch files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from context.schematic_parse import SymbolInstance, _extract_symbol_blocks, _read_properties


@dataclass
class NetLabel:
    """A local or global net label on a schematic sheet."""

    name: str
    sheet_path: str
    kind: str  # label, global_label, hierarchical_label


@dataclass
class SymbolPin:
    """Declared pin on a placed schematic symbol."""

    reference: str
    pin: str
    sheet_path: str
    uuid: str = ""


_LABEL_PATTERN = re.compile(
    r"\((label|global_label|hierarchical_label)\s+\"([^\"]*)\"",
)
_PIN_PATTERN = re.compile(
    r'\(pin\s+"([^"]+)"[^)]*(?:\(uuid\s+"([^"]+)"\))?',
    re.DOTALL,
)


def parse_schematic_labels(schematic_path: Path) -> list[NetLabel]:
    """Parse net labels from a single .kicad_sch file."""
    content = schematic_path.expanduser().read_text(encoding="utf-8")
    sheet_path = schematic_path.name
    labels: list[NetLabel] = []
    for match in _LABEL_PATTERN.finditer(content):
        labels.append(
            NetLabel(
                name=match.group(2),
                sheet_path=sheet_path,
                kind=match.group(1),
            )
        )
    return labels


def parse_schematic_pins(schematic_path: Path) -> list[SymbolPin]:
    """Parse placed symbol pin numbers from a single .kicad_sch file."""
    content = schematic_path.expanduser().read_text(encoding="utf-8")
    sheet_path = schematic_path.name
    pins: list[SymbolPin] = []
    for block in _extract_symbol_blocks(content):
        props = _read_properties(block)
        reference = props.get("Reference", "")
        if not reference:
            continue
        for match in _PIN_PATTERN.finditer(block):
            pins.append(
                SymbolPin(
                    reference=reference,
                    pin=match.group(1),
                    sheet_path=sheet_path,
                    uuid=match.group(2) or "",
                )
            )
    return pins


def parse_project_labels(
    project_root: Path,
    schematic_paths: list[Path],
) -> list[NetLabel]:
    """Parse labels from all given schematic files."""
    all_labels: list[NetLabel] = []
    for sch in schematic_paths:
        resolved = sch if sch.is_absolute() else project_root / sch
        if resolved.is_file():
            all_labels.extend(parse_schematic_labels(resolved))
    return all_labels


def parse_project_pins(
    project_root: Path,
    schematic_paths: list[Path],
) -> list[SymbolPin]:
    """Parse pin declarations from all given schematic files."""
    all_pins: list[SymbolPin] = []
    for sch in schematic_paths:
        resolved = sch if sch.is_absolute() else project_root / sch
        if resolved.is_file():
            all_pins.extend(parse_schematic_pins(resolved))
    return all_pins


def build_pin_connectivity(
    symbols: list[SymbolInstance],
    schematic_pins: list[SymbolPin],
    connectivity_graph: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ref→pin→net map using schematic pins and optional netlist graph."""
    pins_by_ref: dict[str, list[dict[str, str]]] = {}
    for pin in schematic_pins:
        pins_by_ref.setdefault(pin.reference, []).append(
            {"pin": pin.pin, "sheet": pin.sheet_path, "uuid": pin.uuid}
        )

    net_by_ref_pin: dict[tuple[str, str], str] = {}
    if connectivity_graph:
        for entry in connectivity_graph.get("connections") or []:
            if not isinstance(entry, dict):
                continue
            ref = str(entry.get("reference") or "")
            pin = str(entry.get("pin") or "")
            net = str(entry.get("net") or "")
            if ref and pin and net:
                net_by_ref_pin[(ref, pin)] = net

    connections: list[dict[str, str]] = []
    unconnected: list[dict[str, str]] = []
    for sym in symbols:
        if not sym.reference or sym.reference.startswith("#"):
            continue
        for pin_entry in pins_by_ref.get(sym.reference, []):
            pin_num = pin_entry["pin"]
            net = net_by_ref_pin.get((sym.reference, pin_num))
            row = {
                "reference": sym.reference,
                "pin": pin_num,
                "sheet": pin_entry.get("sheet", sym.sheet_path),
                "value": sym.value,
            }
            if net:
                row["net"] = net
                connections.append(row)
            else:
                unconnected.append(row)

    return {
        "pin_count": sum(len(v) for v in pins_by_ref.values()),
        "connected_count": len(connections),
        "unconnected_count": len(unconnected),
        "symbols": pins_by_ref,
        "connections": connections,
        "unconnected_pins": unconnected,
    }


def connectivity_summary(
    labels: list[NetLabel],
    *,
    pin_connectivity: dict[str, Any] | None = None,
) -> dict[str, object]:
    """Compact connectivity summary for prompts."""
    unique_names = sorted({label.name for label in labels if label.name})
    summary: dict[str, object] = {
        "label_count": len(labels),
        "unique_net_names": unique_names,
        "labels": [
            {"name": label.name, "sheet": label.sheet_path, "kind": label.kind}
            for label in labels
        ],
    }
    if pin_connectivity:
        summary["pin_connectivity"] = {
            "pin_count": pin_connectivity.get("pin_count", 0),
            "connected_count": pin_connectivity.get("connected_count", 0),
            "unconnected_count": pin_connectivity.get("unconnected_count", 0),
            "connections": pin_connectivity.get("connections") or [],
            "unconnected_pins": pin_connectivity.get("unconnected_pins") or [],
        }
    return summary
