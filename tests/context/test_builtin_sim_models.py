"""Tests for built-in KiCad simulation model hookups."""

from __future__ import annotations

from pathlib import Path

from context.builtin_sim_models import (
    kicad_simulation_model_incomplete,
    resolve_builtin_simulation_hookup,
)
from context.schematic_parse import SymbolInstance, parse_schematic_symbols
from context.schematic_write import apply_builtin_simulation_models

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_diode_missing_spice_model_is_incomplete() -> None:
    sym = SymbolInstance(
        reference="D1",
        value="1N4007",
        lib_id="Diode:1N4007",
        sim_device="D",
        sim_pins="1=K 2=A",
        sheet_path="p.kicad_sch",
    )
    assert kicad_simulation_model_incomplete(sym)


def test_resolve_diode_builtin_adds_spice_model() -> None:
    sym = SymbolInstance(
        reference="D1",
        value="1N4007",
        lib_id="Diode:1N4007",
        sim_device="D",
        sim_pins="1=K 2=A",
        sheet_path="p.kicad_sch",
    )
    hookup = resolve_builtin_simulation_hookup(sym, "")
    assert hookup is not None
    assert hookup.spice_model == "1N4007"
    assert hookup.spice_primitive == "D"


def test_resistor_without_sim_fields_gets_builtin() -> None:
    sym = SymbolInstance(
        reference="R1",
        value="10K",
        lib_id="Device:R_US",
        sheet_path="p.kicad_sch",
    )
    hookup = resolve_builtin_simulation_hookup(sym, "")
    assert hookup is not None
    assert hookup.sim_device == "R"
    assert hookup.sim_type == "RESISTOR"
    assert "10k" in hookup.sim_params


def test_apply_builtin_simulation_models_writes_diode(tmp_path: Path) -> None:
    sch = tmp_path / "test.kicad_sch"
    sch.write_text((FIXTURES / "testproj.kicad_sch").read_text(encoding="utf-8"), encoding="utf-8")
    pro = tmp_path / "test.kicad_pro"
    pro.touch()
    symbols = parse_schematic_symbols(sch)
    diode = SymbolInstance(
        reference="D9",
        value="1N4007",
        lib_id="Diode:1N4007",
        sim_device="D",
        sim_pins="1=K 2=A",
        sheet_path="test.kicad_sch",
    )
    symbols.append(diode)
    sch_content = sch.read_text(encoding="utf-8")
    sch.write_text(
        sch_content
        + """
\t(symbol
\t\t(lib_id "Diode:1N4007")
\t\t(at 10 10 0)
\t\t(property "Reference" "D9"
\t\t\t(at 10 10 0)
\t\t)
\t\t(property "Value" "1N4007"
\t\t\t(at 10 10 0)
\t\t)
\t\t(property "Sim.Device" "D"
\t\t\t(at 10 10 0)
\t\t)
\t\t(property "Sim.Pins" "1=K 2=A"
\t\t\t(at 10 10 0)
\t\t)
\t\t(pin "1" (uuid "a"))
\t\t(pin "2" (uuid "b"))
\t)
""",
        encoding="utf-8",
    )
    symbols = parse_schematic_symbols(sch)
    result = apply_builtin_simulation_models(pro, symbols)
    assert result.changed_count >= 1
    updated = parse_schematic_symbols(sch)
    d9 = next(s for s in updated if s.reference == "D9")
    assert d9.spice_model == "1N4007"
    assert d9.spice_primitive == "D"
