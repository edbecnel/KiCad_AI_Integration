"""Built-in KiCad/ngspice simulation model hookups for standard schematic symbols."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from context.datasheet_requirements import _STANDARD_DIODE_VALUES, classify_datasheet_requirement
from context.schematic_parse import SymbolInstance
from context.schematic_sim_write import (
    kicad9_sim_hookup_incomplete,
    parse_lib_symbol_pin_names,
)

HookupKind = Literal["subckt", "builtin"]

_NOT_SIMULATED_REF_PREFIXES = ("#",)
_NOT_SIMULATED_LIB_PREFIXES = ("power:",)


@dataclass(frozen=True)
class BuiltinSimHookup:
    """KiCad 9 + legacy SPICE fields for a built-in device model."""

    hookup_kind: HookupKind = "builtin"
    sim_device: str = ""
    sim_type: str = ""
    sim_pins: str = ""
    sim_params: str = ""
    spice_model: str = ""
    spice_primitive: str = ""
    spice_lib: str = ""
    sim_name: str = ""
    sim_library: str = ""


def participates_in_simulation(symbol: SymbolInstance) -> bool:
    """True for schematic instances that KiCad includes in SPICE netlist export."""
    ref = symbol.reference.strip().upper()
    if not ref or ref.startswith(_NOT_SIMULATED_REF_PREFIXES):
        return False
    lib_id = (symbol.lib_id or "").lower()
    if lib_id.startswith(_NOT_SIMULATED_LIB_PREFIXES):
        return False
    value = (symbol.value or "").strip().upper()
    if value in ("GND", "GNDREF", "VCC", "VDD", "VSS"):
        return False
    return True


def _uses_subckt_hookup(symbol: SymbolInstance) -> bool:
    device = symbol.sim_device.strip().upper()
    if device == "SUBCKT" and symbol.sim_library.strip():
        return True
    if device == "SUBCKT" and symbol.spice_lib.strip() and symbol.spice_model.strip():
        return True
    return False


_VALID_SIM_DEVICES = frozenset(
    {"R", "C", "L", "D", "NPN", "PNP", "NJF", "PJF", "NMOS", "PMOS", "V", "I", "SUBCKT", "SPICE"}
)


def kicad_simulation_model_incomplete(symbol: SymbolInstance) -> bool:
    """True when KiCad is likely to report 'No simulation model definition found'."""
    if not participates_in_simulation(symbol):
        return False
    if _uses_subckt_hookup(symbol):
        return kicad9_sim_hookup_incomplete(
            spice_lib=symbol.spice_lib,
            sim_library=symbol.sim_library,
            sim_device=symbol.sim_device,
            sim_name=symbol.sim_name,
            sim_params=symbol.sim_params,
            sim_pins=symbol.sim_pins,
        )

    device = symbol.sim_device.strip().upper()
    if device and device not in _VALID_SIM_DEVICES:
        return True
    if device == "SUBCKT":
        return True
    if device == "R":
        return not symbol.sim_type.strip() and not (
            symbol.spice_model.strip() or symbol.sim_params.strip()
        )
    if device == "C":
        return not symbol.sim_type.strip() and not (
            symbol.spice_model.strip() or symbol.sim_params.strip()
        )
    if device == "L":
        return not symbol.sim_type.strip() and not (
            symbol.spice_model.strip() or symbol.sim_params.strip()
        )
    if device == "D":
        return not symbol.spice_model.strip() and not symbol.sim_params.strip()
    if device in ("NPN", "PNP"):
        return not symbol.sim_type.strip()
    if device == "V":
        return not symbol.sim_type.strip() or not symbol.sim_params.strip()
    if device == "I":
        return not symbol.sim_type.strip() or not symbol.sim_params.strip()
    if device == "SPICE":
        return True
    if not device:
        return True
    return not symbol.sim_type.strip() and not symbol.spice_model.strip()


def _normalize_value_token(value: str) -> str:
    text = value.strip()
    if not text:
        return text
    match = re.match(r"^(\d+(?:\.\d+)?)\s*([a-zA-Zµμ]+)?$", text)
    if not match:
        return text
    number, suffix = match.group(1), (match.group(2) or "")
    suffix = suffix.replace("µ", "u").replace("μ", "u")
    if suffix:
        return f"{number}{suffix.lower()}"
    return number


def _parse_dc_voltage(value: str) -> str | None:
    text = value.strip()
    if not text:
        return None
    match = re.match(r"^(\d+(?:\.\d+)?)\s*V(?:DC|AC)?$", text, re.I)
    if match:
        return match.group(1)
    match = re.match(r"^(\d+(?:\.\d+)?)$", text)
    if match:
        return match.group(1)
    return None


def _default_bjt_pins(
    symbol: SymbolInstance,
    schematic_content: str,
    polarity: str,
) -> str:
    pin_names = parse_lib_symbol_pin_names(schematic_content, symbol.lib_id)
    if polarity == "npn":
        mapping = {"C": "C", "B": "B", "E": "E", "1": "C", "2": "B", "3": "E"}
    else:
        mapping = {"C": "C", "B": "B", "E": "E", "1": "E", "2": "B", "3": "C"}
    if pin_names:
        pairs: list[str] = []
        for num in sorted(pin_names, key=lambda n: int(n) if n.isdigit() else 999):
            name = pin_names[num].upper()
            target = mapping.get(name, mapping.get(num, num))
            pairs.append(f"{num}={target}")
        if pairs:
            return " ".join(pairs)
    return "1=E 2=B 3=C" if polarity == "pnp" else "1=C 2=B 3=E"


def _default_diode_pins(symbol: SymbolInstance, schematic_content: str) -> str:
    if symbol.sim_pins.strip():
        return symbol.sim_pins.strip()
    pin_names = parse_lib_symbol_pin_names(schematic_content, symbol.lib_id)
    if pin_names:
        pairs: list[str] = []
        for num in sorted(pin_names, key=lambda n: int(n) if n.isdigit() else 999):
            name = pin_names[num].upper()
            if name in ("K", "CATHODE"):
                pairs.append(f"{num}=K")
            elif name in ("A", "ANODE"):
                pairs.append(f"{num}=A")
            else:
                pairs.append(f"{num}={name}")
        if pairs:
            return " ".join(pairs)
    return "1=K 2=A"


def resolve_builtin_simulation_hookup(
    symbol: SymbolInstance,
    schematic_content: str,
) -> BuiltinSimHookup | None:
    """
    Build KiCad built-in simulation fields for standard passives and diodes.

    Returns None when the symbol already has a complete model or needs a custom SUBCKT.
    """
    if not participates_in_simulation(symbol):
        return None
    if _uses_subckt_hookup(symbol):
        return None
    if not kicad_simulation_model_incomplete(symbol):
        return None

    lib_id = (symbol.lib_id or "").lower()
    value = (symbol.value or symbol.reference).strip()
    ref = symbol.reference.strip().upper()

    if lib_id.startswith("device:r"):
        if "potentiometer" in lib_id:
            pins = symbol.sim_pins.strip() or "1=r0 2=wiper 3=r1"
            token = _normalize_value_token(value)
            return BuiltinSimHookup(
                sim_device="R",
                sim_type="POT",
                sim_pins=pins,
                spice_primitive="R",
                spice_model=token or value,
                sim_params=f"r={token}" if token else "",
            )
        token = _normalize_value_token(value)
        return BuiltinSimHookup(
            sim_device="R",
            sim_type="RESISTOR",
            sim_pins=symbol.sim_pins.strip() or "1=1 2=2",
            spice_primitive="R",
            spice_model=token or value,
            sim_params=f"r={token}" if token else "",
        )

    if lib_id.startswith("device:c"):
        token = _normalize_value_token(value)
        return BuiltinSimHookup(
            sim_device="C",
            sim_type="CAPACITOR",
            sim_pins=symbol.sim_pins.strip() or "1=1 2=2",
            spice_primitive="C",
            spice_model=token or value,
            sim_params=f"c={token}" if token else "",
        )

    if lib_id.startswith("device:l"):
        token = _normalize_value_token(value)
        return BuiltinSimHookup(
            sim_device="L",
            sim_type="INDUCTOR",
            sim_pins=symbol.sim_pins.strip() or "1=1 2=2",
            spice_primitive="L",
            spice_model=token or value,
            sim_params=f"l={token}" if token else "",
        )

    if lib_id.startswith("device:d") or lib_id.startswith("diode:"):
        model = value or "D"
        return BuiltinSimHookup(
            sim_device="D",
            sim_pins=_default_diode_pins(symbol, schematic_content),
            spice_primitive="D",
            spice_model=model,
        )

    if ref.startswith("D") and _STANDARD_DIODE_VALUES.match(value):
        model = value or "D"
        return BuiltinSimHookup(
            sim_device="D",
            sim_pins=_default_diode_pins(symbol, schematic_content),
            spice_primitive="D",
            spice_model=model,
        )

    if lib_id.startswith("device:led"):
        return BuiltinSimHookup(
            sim_device="D",
            sim_pins=_default_diode_pins(symbol, schematic_content),
            spice_primitive="D",
            spice_model=value or "LED",
            sim_params="",
        )

    if lib_id.startswith("device:battery") or ref.startswith("BT"):
        voltage = _parse_dc_voltage(value)
        if voltage is None:
            return None
        return BuiltinSimHookup(
            sim_device="V",
            sim_type="DC",
            sim_pins=symbol.sim_pins.strip() or "1=+ 2=-",
            spice_primitive="V",
            spice_model=value,
            sim_params=f"dc={voltage}",
        )

    if classify_datasheet_requirement(symbol) == "required":
        if symbol.spice_lib.strip() or symbol.sim_library.strip():
            return None
        lib_hint = lib_id
        if "npn" in lib_hint or symbol.sim_device.upper() == "NPN":
            return BuiltinSimHookup(
                sim_device="NPN",
                sim_type="GUMMELPOON",
                sim_pins=_default_bjt_pins(symbol, schematic_content, "npn"),
                spice_primitive="Q",
                spice_model=value,
            )
        if "pnp" in lib_hint or symbol.sim_device.upper() == "PNP":
            return BuiltinSimHookup(
                sim_device="PNP",
                sim_type="GUMMELPOON",
                sim_pins=_default_bjt_pins(symbol, schematic_content, "pnp"),
                spice_primitive="Q",
                spice_model=value,
            )
        return None

    if "npn" in lib_id and not symbol.sim_device.strip():
        return BuiltinSimHookup(
            sim_device="NPN",
            sim_type="GUMMELPOON",
            sim_pins=_default_bjt_pins(symbol, schematic_content, "npn"),
            spice_primitive="Q",
            spice_model=value,
        )
    if "pnp" in lib_id and not symbol.sim_device.strip():
        return BuiltinSimHookup(
            sim_device="PNP",
            sim_type="GUMMELPOON",
            sim_pins=_default_bjt_pins(symbol, schematic_content, "pnp"),
            spice_primitive="Q",
            spice_model=value,
        )

    return None
