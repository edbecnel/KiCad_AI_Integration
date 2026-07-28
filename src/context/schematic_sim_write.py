"""KiCad 9 simulation model field helpers (Sim.Device / Sim.Library / Sim.Name / Sim.Pins)."""

from __future__ import annotations

import re
from pathlib import Path

# Map common schematic pin names to SUBCKT node names (case-insensitive).
_PIN_SEMANTIC_ALIASES: dict[str, tuple[str, ...]] = {
    "gate": ("g", "gate"),
    "drain": ("d", "drain"),
    "source": ("s", "source"),
    "anode": ("a", "anode"),
    "cathode": ("k", "cathode"),
    "collector": ("c", "collector"),
    "emitter": ("e", "emitter"),
    "base": ("b", "base"),
}


def parse_subckt_name_and_pins(lib_text: str, preferred_name: str | None = None) -> tuple[str | None, list[str]]:
    """Return (subckt_name, pin_names) from the first matching .SUBCKT line."""
    preferred = (preferred_name or "").strip()
    matches: list[tuple[str, list[str]]] = []
    for line in lib_text.splitlines():
        stripped = line.strip()
        if not stripped.upper().startswith(".SUBCKT"):
            continue
        tokens = stripped.split()
        if len(tokens) < 2:
            continue
        name = tokens[1]
        pins = tokens[2:]
        matches.append((name, pins))
        if preferred and name == preferred:
            return name, pins
    if not matches:
        return None, []
    return matches[0]


def parse_lib_symbol_pin_names(schematic_content: str, lib_id: str) -> dict[str, str]:
    """
    Parse symbol pin number → pin name from ``lib_symbols`` for a ``lib_id``.

    Example: ``{"1": "G", "2": "D", "3": "S"}`` for a MOSFET.
    """
    if not lib_id.strip():
        return {}
    lib_start = schematic_content.find("(lib_symbols")
    if lib_start == -1:
        return {}
    depth = 0
    lib_end = lib_start
    for pos in range(lib_start, len(schematic_content)):
        if schematic_content[pos] == "(":
            depth += 1
        elif schematic_content[pos] == ")":
            depth -= 1
            if depth == 0:
                lib_end = pos + 1
                break
    lib_section = schematic_content[lib_start:lib_end]
    marker = f'(symbol "{lib_id}"'
    sym_start = lib_section.find(marker)
    if sym_start == -1:
        return {}
    sym_depth = 0
    sym_end = sym_start
    for pos in range(sym_start, len(lib_section)):
        if lib_section[pos] == "(":
            sym_depth += 1
        elif lib_section[pos] == ")":
            sym_depth -= 1
            if sym_depth == 0:
                sym_end = pos + 1
                break
    symbol_def = lib_section[sym_start:sym_end]
    pin_map: dict[str, str] = {}
    pos = 0
    while pos < len(symbol_def):
        pin_idx = symbol_def.find("(pin ", pos)
        if pin_idx == -1:
            break
        depth = 0
        pin_end = pin_idx
        for i in range(pin_idx, len(symbol_def)):
            ch = symbol_def[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    pin_end = i + 1
                    break
        block = symbol_def[pin_idx:pin_end]
        name_match = re.search(r'\(name\s+"([^"]*)"', block)
        num_match = re.search(r'\(number\s+"([^"]*)"', block)
        if num_match:
            pin_map[num_match.group(1)] = name_match.group(1) if name_match else num_match.group(1)
        pos = pin_end
    return pin_map


def _match_subckt_pin(symbol_pin_name: str, subckt_pins: list[str]) -> str | None:
    sym = symbol_pin_name.strip()
    sym_upper = sym.upper()
    sym_lower = sym.lower()
    for sub_pin in subckt_pins:
        if sub_pin.lower() == sym_lower or sub_pin.upper() == sym_upper:
            return sub_pin
    for sub_pin in subckt_pins:
        if len(sym) == 1 and sub_pin.lower().startswith(sym_lower):
            return sub_pin
    for canonical, aliases in _PIN_SEMANTIC_ALIASES.items():
        if sym_lower in aliases or sym_upper in {a.upper() for a in aliases}:
            for sub_pin in subckt_pins:
                if sub_pin.lower() == canonical or sub_pin.lower().startswith(canonical[0]):
                    return sub_pin
    return None


def build_sim_pins_mapping(
    symbol_pin_names: dict[str, str],
    subckt_pin_names: list[str],
) -> str:
    """Build KiCad ``Sim.Pins`` value: ``1=gate 2=drain 3=source``."""
    if not subckt_pin_names:
        return ""
    pairs: list[str] = []
    for num in sorted(symbol_pin_names, key=lambda n: int(n) if n.isdigit() else 9999):
        sym_name = symbol_pin_names[num]
        target = _match_subckt_pin(sym_name, subckt_pin_names)
        if target is None:
            idx = int(num) - 1 if num.isdigit() else -1
            if 0 <= idx < len(subckt_pin_names):
                target = subckt_pin_names[idx]
            else:
                target = subckt_pin_names[min(len(pairs), len(subckt_pin_names) - 1)]
        pairs.append(f"{num}={target}")
    if not pairs and subckt_pin_names:
        pairs = [f"{i + 1}={name}" for i, name in enumerate(subckt_pin_names)]
    return " ".join(pairs)


def load_subckt_metadata(lib_path: Path, preferred_name: str | None = None) -> tuple[str, list[str]]:
    """Read a .lib file and return subckt name and pin list."""
    text = lib_path.expanduser().resolve().read_text(encoding="utf-8", errors="replace")
    name, pins = parse_subckt_name_and_pins(text, preferred_name)
    if name is None:
        safe = (preferred_name or "PART").strip()
        return safe, pins
    return name, pins


def kicad9_sim_hookup_incomplete(
    *,
    spice_lib: str = "",
    sim_library: str = "",
    sim_device: str = "",
    sim_name: str = "",
    sim_params: str = "",
    sim_pins: str = "",
) -> bool:
    """True when a .lib path exists but KiCad 9 Sim.* hookup is not configured."""
    has_lib_path = bool(spice_lib.strip() or sim_library.strip())
    if not has_lib_path:
        return False
    device = sim_device.strip().upper()
    if device == "SPICE":
        return True
    if sim_params.strip() and ('lib=""' in sim_params or "lib=''" in sim_params):
        return True
    if device == "SUBCKT" and sim_library.strip() and sim_name.strip():
        if sim_pins.strip():
            return False
        return True
    if sim_params.strip() and 'lib=""' not in sim_params and "lib=''" not in sim_params:
        if "lib=" in sim_params.lower() and sim_library.strip():
            return False
    return True
