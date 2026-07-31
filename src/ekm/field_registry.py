"""EKM field-type registry for notebook presentation (ADP-003 §9.1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ekm.model import FIELD_TYPES, KICAD_LINK_KINDS

ValueShape = str  # text | enum | number | measurement | reference | attachment


@dataclass(frozen=True)
class FieldEditorSpec:
    """Presentation metadata for one EKM primitive field type."""

    field_type: str
    editor_kind: str
    value_shape: ValueShape
    editable: bool
    format_display: Callable[[Any, dict[str, Any]], str]


def _format_text(value: Any, metadata: dict[str, Any]) -> str:
    if metadata.get("question"):
        return f"{metadata['question']} [{value}]"
    return str(value) if value is not None else ""


def _format_number(value: Any, metadata: dict[str, Any]) -> str:
    unit = metadata.get("unit") or ""
    if value is None:
        return ""
    text = str(value)
    return f"{text} {unit}".strip() if unit else text


def _format_enum(value: Any, metadata: dict[str, Any]) -> str:
    return _format_text(value, metadata)


def _format_measurement(value: Any, _metadata: dict[str, Any]) -> str:
    if not isinstance(value, dict):
        return str(value)
    parts = [str(value.get("value", "")), str(value.get("unit", "")).strip()]
    text = " ".join(p for p in parts if p)
    conditions = value.get("conditions")
    if isinstance(conditions, str) and conditions.strip():
        text += f" ({conditions})"
    return text


def _format_reference(value: Any, _metadata: dict[str, Any]) -> str:
    if not isinstance(value, dict):
        return str(value)
    kind = value.get("kind", "")
    ref = value.get("ref", "")
    sheet = value.get("sheet_path")
    if sheet:
        return f"{kind}: {ref} @ {sheet}"
    return f"{kind}: {ref}"


def _format_attachment(value: Any, _metadata: dict[str, Any]) -> str:
    if isinstance(value, dict):
        artifact_id = value.get("artifact_id")
        if artifact_id:
            return str(artifact_id)
    return str(value) if value is not None else ""


_FIELD_SPECS: dict[str, FieldEditorSpec] = {
    "text": FieldEditorSpec("text", "text", "text", True, _format_text),
    "enum": FieldEditorSpec("enum", "enum", "enum", True, _format_enum),
    "number": FieldEditorSpec("number", "number", "number", True, _format_number),
    "measurement": FieldEditorSpec(
        "measurement", "measurement", "measurement", True, _format_measurement
    ),
    "reference": FieldEditorSpec("reference", "reference", "reference", True, _format_reference),
    "attachment": FieldEditorSpec(
        "attachment", "attachment", "attachment", False, _format_attachment
    ),
}

_READONLY_SPEC = FieldEditorSpec("unknown", "readonly", "text", False, _format_text)


def get_field_editor_spec(field_type: str) -> FieldEditorSpec:
    """Return registry entry for an EKM field type."""
    return _FIELD_SPECS.get(field_type, _READONLY_SPEC)


def editor_kind_for_type(field_type: str) -> str:
    return get_field_editor_spec(field_type).editor_kind


def format_field_display(
    field_type: str,
    value: Any,
    *,
    metadata: dict[str, Any] | None = None,
    attachment_resolver: Callable[[str], str] | None = None,
) -> str:
    """Format a field value for readonly display."""
    spec = get_field_editor_spec(field_type)
    if field_type == "attachment" and attachment_resolver is not None:
        artifact_id = ""
        if isinstance(value, dict):
            artifact_id = str(value.get("artifact_id") or "")
        if artifact_id:
            return attachment_resolver(artifact_id)
    return spec.format_display(value, metadata or {})


def parse_number_input(text: str) -> float:
    stripped = text.strip()
    if not stripped:
        raise ValueError("Number value is required")
    return float(stripped)


def parse_measurement_input(
    value_text: str,
    unit_text: str,
    conditions_text: str = "",
) -> dict[str, Any]:
    value = parse_number_input(value_text)
    unit = unit_text.strip()
    if not unit:
        raise ValueError("Measurement unit is required")
    payload: dict[str, Any] = {"value": value, "unit": unit}
    conditions = conditions_text.strip()
    if conditions:
        payload["conditions"] = conditions
    return payload


def parse_reference_input(
    kind: str,
    ref: str,
    sheet_path: str = "",
) -> dict[str, Any]:
    if kind not in KICAD_LINK_KINDS:
        raise ValueError(f"Reference kind must be one of {sorted(KICAD_LINK_KINDS)}")
    reference = ref.strip()
    if not reference:
        raise ValueError("Reference ref is required")
    payload: dict[str, Any] = {"kind": kind, "ref": reference}
    sheet = sheet_path.strip()
    if sheet:
        payload["sheet_path"] = sheet
    return payload


def supported_field_types() -> frozenset[str]:
    return FIELD_TYPES
