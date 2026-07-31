"""Tests for EKM field registry."""

from __future__ import annotations

import pytest

from ekm.field_registry import (
    format_field_display,
    get_field_editor_spec,
    parse_measurement_input,
    parse_number_input,
    parse_reference_input,
)


def test_registry_editor_kinds() -> None:
    assert get_field_editor_spec("text").editor_kind == "text"
    assert get_field_editor_spec("attachment").editable is False
    assert get_field_editor_spec("measurement").editable is True


def test_format_measurement_display() -> None:
    text = format_field_display(
        "measurement",
        {"value": 3.3, "unit": "V", "conditions": "no load"},
    )
    assert "3.3" in text
    assert "V" in text
    assert "no load" in text


def test_parse_number_input() -> None:
    assert parse_number_input("12.5") == 12.5
    with pytest.raises(ValueError):
        parse_number_input("")


def test_parse_measurement_input() -> None:
    payload = parse_measurement_input("1.2", "A", "T=25C")
    assert payload == {"value": 1.2, "unit": "A", "conditions": "T=25C"}


def test_parse_reference_input() -> None:
    payload = parse_reference_input("component", "Q1", "root.kicad_sch")
    assert payload == {"kind": "component", "ref": "Q1", "sheet_path": "root.kicad_sch"}
