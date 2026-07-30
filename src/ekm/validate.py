"""Structural validation for EKM documents (stdlib-only; mirrors ekm_schema_v1.json)."""

from __future__ import annotations

import re
from typing import Any

from ekm.errors import EKMValidationError, EKMVersionError
from ekm.model import (
    FIELD_TYPES,
    KICAD_LINK_KINDS,
    SUPPORTED_SCHEMA_VERSION,
    EKMDocument,
)

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def parse_schema_version(version: str) -> tuple[int, int, int]:
    if not _SEMVER_RE.match(version):
        raise EKMVersionError(f"Invalid schema_version format: {version!r}")
    major, minor, patch = (int(x) for x in version.split("."))
    return major, minor, patch


def assert_supported_version(version: str) -> None:
    doc_major, _, _ = parse_schema_version(version)
    supported_major, _, _ = parse_schema_version(SUPPORTED_SCHEMA_VERSION)
    if doc_major != supported_major:
        raise EKMVersionError(
            f"Unsupported EKM major version {version!r}; "
            f"supported: {SUPPORTED_SCHEMA_VERSION}"
        )


def _require_str(obj: dict[str, Any], key: str, *, path: str) -> str:
    val = obj.get(key)
    if not isinstance(val, str) or not val.strip():
        raise EKMValidationError(f"{path}.{key} must be a non-empty string")
    return val


def _validate_kicad_link(link: Any, *, path: str) -> None:
    if not isinstance(link, dict):
        raise EKMValidationError(f"{path} must be an object")
    kind = link.get("kind")
    if kind not in KICAD_LINK_KINDS:
        raise EKMValidationError(f"{path}.kind must be one of {sorted(KICAD_LINK_KINDS)}")
    ref = link.get("ref")
    if not isinstance(ref, str) or not ref.strip():
        raise EKMValidationError(f"{path}.ref must be a non-empty string")
    sheet_path = link.get("sheet_path")
    if sheet_path is not None and not isinstance(sheet_path, str):
        raise EKMValidationError(f"{path}.sheet_path must be a string or omitted")


def _validate_field(field: Any, *, path: str) -> None:
    if not isinstance(field, dict):
        raise EKMValidationError(f"{path} must be an object")
    _require_str(field, "id", path=path)
    ftype = field.get("type")
    if ftype not in FIELD_TYPES:
        raise EKMValidationError(f"{path}.type must be one of {sorted(FIELD_TYPES)}")
    if "value" not in field:
        raise EKMValidationError(f"{path}.value is required")
    if ftype == "text" and not isinstance(field["value"], str):
        raise EKMValidationError(f"{path}.value must be a string for text fields")
    if ftype == "number" and not isinstance(field["value"], (int, float)):
        raise EKMValidationError(f"{path}.value must be a number")
    if ftype == "enum":
        options = field.get("options")
        if not isinstance(options, list) or not options:
            raise EKMValidationError(f"{path}.options must be a non-empty array")
        if not isinstance(field["value"], str):
            raise EKMValidationError(f"{path}.value must be a string for enum fields")
    if ftype == "reference":
        _validate_kicad_link(field["value"], path=f"{path}.value")
    if ftype == "measurement":
        mv = field["value"]
        if not isinstance(mv, dict):
            raise EKMValidationError(f"{path}.value must be a measurement object")
        if not isinstance(mv.get("value"), (int, float)):
            raise EKMValidationError(f"{path}.value.value must be a number")
        unit = mv.get("unit")
        if not isinstance(unit, str) or not unit.strip():
            raise EKMValidationError(f"{path}.value.unit must be a non-empty string")
    if ftype == "attachment":
        av = field["value"]
        if not isinstance(av, dict):
            raise EKMValidationError(f"{path}.value must be an attachment object")
        aid = av.get("artifact_id")
        if not isinstance(aid, str) or not aid.strip():
            raise EKMValidationError(f"{path}.value.artifact_id must be a non-empty string")
    links = field.get("links")
    if links is not None:
        if not isinstance(links, list):
            raise EKMValidationError(f"{path}.links must be an array")
        for i, link in enumerate(links):
            _validate_kicad_link(link, path=f"{path}.links[{i}]")


def _validate_section(section: Any, *, path: str, seen_ids: set[str]) -> None:
    if not isinstance(section, dict):
        raise EKMValidationError(f"{path} must be an object")
    sid = _require_str(section, "id", path=path)
    if sid in seen_ids:
        raise EKMValidationError(f"Duplicate section id: {sid!r}")
    seen_ids.add(sid)
    _require_str(section, "title", path=path)
    fields = section.get("fields")
    if not isinstance(fields, list):
        raise EKMValidationError(f"{path}.fields must be an array")
    field_ids: set[str] = set()
    for i, fld in enumerate(fields):
        if isinstance(fld, dict):
            fid = fld.get("id")
            if isinstance(fid, str) and fid in field_ids:
                raise EKMValidationError(f"Duplicate field id {fid!r} in section {sid!r}")
            if isinstance(fid, str):
                field_ids.add(fid)
        _validate_field(fld, path=f"{path}.fields[{i}]")


def validate_document_data(data: dict[str, Any]) -> EKMDocument:
    """Validate raw dict and return EKMDocument."""
    if not isinstance(data, dict):
        raise EKMValidationError("EKM document must be a JSON object")
    extra = set(data.keys()) - {"schema_version", "sections", "project_path", "updated_at"}
    if extra:
        raise EKMValidationError(f"Unknown top-level keys: {sorted(extra)}")
    if "schema_version" not in data:
        raise EKMVersionError("Missing required schema_version")
    version = str(data["schema_version"])
    assert_supported_version(version)
    sections = data.get("sections")
    if not isinstance(sections, list):
        raise EKMValidationError("sections must be an array")
    seen: set[str] = set()
    for i, section in enumerate(sections):
        _validate_section(section, path=f"sections[{i}]", seen_ids=seen)
    project_path = data.get("project_path")
    if project_path is not None and not isinstance(project_path, str):
        raise EKMValidationError("project_path must be a string or omitted")
    updated_at = data.get("updated_at")
    if updated_at is not None and not isinstance(updated_at, str):
        raise EKMValidationError("updated_at must be a string or omitted")
    return EKMDocument.from_dict(data)


def validate_document(doc: EKMDocument) -> None:
    validate_document_data(doc.to_dict())
