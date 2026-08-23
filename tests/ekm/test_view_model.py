"""Tests for EKM View Model."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ekm import EKMValidationError, EKMViewModel, init_empty, save
from ekm.model import EKMDocument


def _doc_with_sections() -> EKMDocument:
    return EKMDocument.from_dict(
        {
            "schema_version": "1.0.0",
            "sections": [
                {
                    "id": "circuit_overview",
                    "title": "Circuit Overview",
                    "order": 0,
                    "fields": [
                        {
                            "id": "summary",
                            "type": "text",
                            "label": "Summary",
                            "value": "Blocking oscillator",
                        }
                    ],
                },
                {
                    "id": "open_items",
                    "title": "Open Items",
                    "order": 6,
                    "fields": [
                        {
                            "id": "q1",
                            "type": "enum",
                            "label": "Open question",
                            "value": "Pending Review",
                            "options": ["Pending Review", "Resolved", "Deferred"],
                            "metadata": {
                                "question": "What is the measured switching frequency?",
                            },
                        }
                    ],
                },
            ],
        }
    )


def test_from_project_empty(tmp_path: Path) -> None:
    vm = EKMViewModel.from_project(tmp_path)
    assert vm.sections() == []
    assert vm.dirty is False


def test_sections_sorted_by_order() -> None:
    vm = EKMViewModel(document=_doc_with_sections(), project_path=Path("/tmp/p"))
    sections = vm.sections()
    assert [s.section_id for s in sections] == ["circuit_overview", "open_items"]
    assert sections[0].fields[0].label == "Summary"
    assert sections[0].fields[0].editor_kind == "text"
    assert sections[1].fields[0].label == "What is the measured switching frequency?"


def test_update_text_field_marks_dirty() -> None:
    vm = EKMViewModel(document=_doc_with_sections(), project_path=Path("/tmp/p"))
    vm.update_text_field("circuit_overview", "summary", "Updated summary")
    assert vm.dirty is True
    assert vm.sections()[0].fields[0].value == "Updated summary"


def test_update_enum_field_validates_options() -> None:
    vm = EKMViewModel(document=_doc_with_sections(), project_path=Path("/tmp/p"))
    vm.update_enum_field("open_items", "q1", "Resolved")
    assert vm.sections()[1].fields[0].value == "Resolved"
    with pytest.raises(EKMValidationError):
        vm.update_enum_field("open_items", "q1", "bogus")


def test_save_round_trip(tmp_path: Path) -> None:
    init_empty(tmp_path)
    vm = EKMViewModel.from_project(tmp_path)
    vm.document = _doc_with_sections()
    vm.dirty = True
    path = vm.save()
    reloaded = EKMViewModel.from_project(path)
    assert reloaded.dirty is False
    assert reloaded.sections()[0].fields[0].value == "Blocking oscillator"


def test_reload_discards_edits(tmp_path: Path) -> None:
    doc = _doc_with_sections()
    path = save(doc, tmp_path / "kicad_ai" / "engineering_knowledge.json")
    vm = EKMViewModel.from_project(path)
    vm.update_text_field("circuit_overview", "summary", "Transient edit")
    vm.reload()
    assert vm.dirty is False
    assert vm.sections()[0].fields[0].value == "Blocking oscillator"


def test_full_primitives_fixture() -> None:
    fixture = Path(__file__).parent / "fixtures" / "full_primitives.json"
    data = json.loads(fixture.read_text(encoding="utf-8"))
    vm = EKMViewModel(document=EKMDocument.from_dict(data), project_path=Path("/tmp/p"))
    section = vm.sections()[0]
    kinds = {fld.editor_kind for fld in section.fields}
    assert kinds == {"text", "enum", "number", "measurement", "reference", "attachment"}


def test_update_number_measurement_reference() -> None:
    fixture = Path(__file__).parent / "fixtures" / "full_primitives.json"
    data = json.loads(fixture.read_text(encoding="utf-8"))
    vm = EKMViewModel(document=EKMDocument.from_dict(data), project_path=Path("/tmp/p"))
    vm.update_number_field("primitives", "turns", 15)
    vm.update_measurement_field("primitives", "v_peak", 5.0, "V", conditions="loaded")
    vm.update_reference_field("primitives", "primary_switch", "net", "VCC")
    section = vm.sections()[0]
    by_id = {fld.field_id: fld for fld in section.fields}
    assert by_id["turns"].value == 15
    assert by_id["v_peak"].value["value"] == 5.0
    assert by_id["primary_switch"].value["kind"] == "net"


def test_attachment_display_resolver() -> None:
    fixture = Path(__file__).parent / "fixtures" / "full_primitives.json"
    data = json.loads(fixture.read_text(encoding="utf-8"))
    vm = EKMViewModel.from_project(
        Path("/tmp/p"),
        attachment_resolver=lambda aid: f"resolved:{aid}",
    )
    vm.document = EKMDocument.from_dict(data)
    field = vm.sections()[0].fields[-1]
    assert field.display_value == "resolved:ds-abc123"


def test_search_hits_section_and_field() -> None:
    vm = EKMViewModel(document=_doc_with_sections(), project_path=Path("/tmp/p"))
    hits = vm.search("Blocking")
    assert any(hit.field_id == "summary" for hit in hits)
    section_hits = vm.search("Open Items")
    assert any(hit.field_id is None for hit in section_hits)


def test_filter_sections_by_query() -> None:
    vm = EKMViewModel(document=_doc_with_sections(), project_path=Path("/tmp/p"))
    vm.set_filter_query("open")
    sections = vm.sections()
    assert len(sections) == 1
    assert sections[0].section_id == "open_items"
