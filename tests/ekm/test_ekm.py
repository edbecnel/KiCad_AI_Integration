"""Tests for EKM validation and I/O."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ekm import EKMDocument, EKMValidationError, EKMVersionError, init_empty, load, save
from ekm.validate import validate_document_data


def test_empty_document_round_trip(tmp_path: Path) -> None:
    out = init_empty(tmp_path)
    doc = load(out)
    assert doc.schema_version == "1.0.0"
    assert doc.sections == []


def test_save_atomic(tmp_path: Path) -> None:
    doc = EKMDocument.empty()
    doc.sections.append(
        {
            "id": "s1",
            "title": "Overview",
            "fields": [{"id": "f1", "type": "text", "value": "hello"}],
        }
    )
    path = save(doc, tmp_path / "kicad_ai" / "engineering_knowledge.json")
    assert path.is_file()
    reloaded = load(path)
    assert reloaded.sections[0]["title"] == "Overview"


def test_rejects_unknown_major_version() -> None:
    with pytest.raises(EKMVersionError):
        validate_document_data({"schema_version": "2.0.0", "sections": []})


def test_rejects_invalid_field_type() -> None:
    with pytest.raises(EKMValidationError):
        validate_document_data(
            {
                "schema_version": "1.0.0",
                "sections": [
                    {
                        "id": "s1",
                        "title": "T",
                        "fields": [{"id": "f1", "type": "bogus", "value": "x"}],
                    }
                ],
            }
        )


def test_fixture_valid_minimal() -> None:
    fixture = Path(__file__).parent / "fixtures" / "minimal_valid.json"
    data = json.loads(fixture.read_text(encoding="utf-8"))
    doc = validate_document_data(data)
    assert doc.schema_version == "1.0.0"
