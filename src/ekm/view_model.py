"""EKM View Model — UI-agnostic edit and validation layer (ADP-003)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ekm.errors import EKMError, EKMValidationError
from ekm.field_registry import (
    editor_kind_for_type,
    format_field_display,
    get_field_editor_spec,
    parse_measurement_input,
    parse_number_input,
    parse_reference_input,
)
from ekm.io import load, save
from ekm.model import EKMDocument, KICAD_LINK_KINDS
from ekm.paths import resolve_ekm_path
from ekm.validate import validate_document_data


@dataclass
class FieldView:
    """Presentation-ready view of one EKM field."""

    section_id: str
    field_id: str
    label: str
    field_type: str
    editor_kind: str
    value: Any
    options: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
    editable: bool = True
    display_value: str = ""


@dataclass
class SectionView:
    """Presentation-ready view of one EKM section."""

    section_id: str
    title: str
    order: int
    fields: list[FieldView] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchHit:
    """One notebook search match."""

    section_id: str
    section_title: str
    field_id: str | None
    field_label: str | None
    snippet: str


def _field_label(section_title: str, fld: dict[str, Any]) -> str:
    metadata = fld.get("metadata") or {}
    question = metadata.get("question")
    if isinstance(question, str) and question.strip():
        return question.strip()
    label = fld.get("label")
    if isinstance(label, str) and label.strip():
        return label.strip()
    return f"{section_title} — {fld.get('id', 'field')}"


def _build_field_view(
    section: dict[str, Any],
    fld: dict[str, Any],
    *,
    attachment_resolver: Callable[[str], str] | None = None,
) -> FieldView:
    section_id = str(section["id"])
    section_title = str(section.get("title") or section_id)
    field_id = str(fld["id"])
    field_type = str(fld.get("type") or "text")
    options = fld.get("options")
    metadata = dict(fld.get("metadata") or {})
    spec = get_field_editor_spec(field_type)
    value = fld.get("value")
    return FieldView(
        section_id=section_id,
        field_id=field_id,
        label=_field_label(section_title, fld),
        field_type=field_type,
        editor_kind=spec.editor_kind,
        value=value,
        options=list(options) if isinstance(options, list) else [],
        metadata=metadata,
        raw=dict(fld),
        editable=spec.editable,
        display_value=format_field_display(
            field_type,
            value,
            metadata=metadata,
            attachment_resolver=attachment_resolver,
        ),
    )


def _build_section_view(
    section: dict[str, Any],
    *,
    attachment_resolver: Callable[[str], str] | None = None,
) -> SectionView:
    fields_raw = section.get("fields") or []
    fields = [
        _build_field_view(section, fld, attachment_resolver=attachment_resolver)
        for fld in fields_raw
        if isinstance(fld, dict)
    ]
    return SectionView(
        section_id=str(section["id"]),
        title=str(section.get("title") or section["id"]),
        order=int(section.get("order") or 0),
        fields=fields,
        raw=dict(section),
    )


@dataclass
class EKMViewModel:
    """Translate between EKM documents and notebook presentation state."""

    document: EKMDocument
    project_path: Path
    dirty: bool = False
    last_error: str | None = None
    _filter_query: str | None = None
    _attachment_resolver: Callable[[str], str] | None = None

    @classmethod
    def from_project(
        cls,
        project_path: Path | str,
        *,
        attachment_resolver: Callable[[str], str] | None = None,
    ) -> EKMViewModel:
        path = Path(project_path).expanduser()
        ekm_path = resolve_ekm_path(path)
        if ekm_path.is_file():
            doc = load(path)
        else:
            project_ref = str(path) if path.suffix == ".kicad_pro" else str(ekm_path.parent.parent)
            doc = EKMDocument.empty(project_path=project_ref)
        return cls(
            document=doc,
            project_path=path,
            _attachment_resolver=attachment_resolver,
        )

    def set_attachment_resolver(self, resolver: Callable[[str], str] | None) -> None:
        self._attachment_resolver = resolver

    def resolve_attachment_display(self, artifact_id: str) -> str:
        if self._attachment_resolver is not None:
            return self._attachment_resolver(artifact_id)
        return artifact_id

    def sections(self, *, section_ids: list[str] | None = None) -> list[SectionView]:
        views = [
            _build_section_view(section, attachment_resolver=self._attachment_resolver)
            for section in self.document.sections
        ]
        views.sort(key=lambda s: (s.order, s.title.lower()))
        if section_ids is not None:
            allowed = set(section_ids)
            views = [view for view in views if view.section_id in allowed]
        if self._filter_query:
            query = self._filter_query.casefold()
            filtered: list[SectionView] = []
            for view in views:
                matching_fields = [
                    fld
                    for fld in view.fields
                    if query in fld.label.casefold()
                    or query in fld.display_value.casefold()
                    or query in fld.field_id.casefold()
                ]
                if (
                    query in view.title.casefold()
                    or query in view.section_id.casefold()
                    or matching_fields
                ):
                    copy = SectionView(
                        section_id=view.section_id,
                        title=view.title,
                        order=view.order,
                        fields=matching_fields or view.fields,
                        raw=view.raw,
                    )
                    filtered.append(copy)
            views = filtered
        return views

    def set_filter_query(self, query: str | None) -> None:
        self._filter_query = query.strip() if query and query.strip() else None

    def search(self, query: str) -> list[SearchHit]:
        needle = query.strip().casefold()
        if not needle:
            return []
        hits: list[SearchHit] = []
        for section in self.sections():
            if needle in section.title.casefold() or needle in section.section_id.casefold():
                hits.append(
                    SearchHit(
                        section_id=section.section_id,
                        section_title=section.title,
                        field_id=None,
                        field_label=None,
                        snippet=section.title,
                    )
                )
            for fld in section.fields:
                haystacks = [
                    fld.label,
                    fld.display_value,
                    fld.field_id,
                    str(fld.value),
                ]
                if any(needle in str(item).casefold() for item in haystacks):
                    hits.append(
                        SearchHit(
                            section_id=section.section_id,
                            section_title=section.title,
                            field_id=fld.field_id,
                            field_label=fld.label,
                            snippet=fld.display_value or str(fld.value),
                        )
                    )
        return hits

    def summary(self) -> dict[str, Any]:
        field_counts: dict[str, int] = {}
        for section in self.document.sections:
            for fld in section.get("fields") or []:
                if isinstance(fld, dict):
                    ftype = str(fld.get("type") or "unknown")
                    field_counts[ftype] = field_counts.get(ftype, 0) + 1
        return {
            "schema_version": self.document.schema_version,
            "section_count": len(self.document.sections),
            "field_type_counts": field_counts,
            "dirty": self.dirty,
            "project_path": self.document.project_path,
            "updated_at": self.document.updated_at,
            "filter_query": self._filter_query,
        }

    def _find_field(self, section_id: str, field_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        for section in self.document.sections:
            if section.get("id") != section_id:
                continue
            for fld in section.get("fields") or []:
                if isinstance(fld, dict) and fld.get("id") == field_id:
                    return section, fld
        raise KeyError(f"Field {section_id}/{field_id} not found")

    def _validate_and_mark_dirty(self) -> None:
        validate_document_data(self.document.to_dict())
        self.dirty = True
        self.last_error = None

    def update_text_field(self, section_id: str, field_id: str, value: str) -> None:
        _section, fld = self._find_field(section_id, field_id)
        if fld.get("type") != "text":
            raise EKMValidationError(f"Field {field_id!r} is not a text field")
        fld["value"] = value
        self._validate_and_mark_dirty()

    def update_enum_field(self, section_id: str, field_id: str, value: str) -> None:
        _section, fld = self._find_field(section_id, field_id)
        if fld.get("type") != "enum":
            raise EKMValidationError(f"Field {field_id!r} is not an enum field")
        options = fld.get("options")
        if not isinstance(options, list) or value not in options:
            raise EKMValidationError(f"Value {value!r} is not in enum options")
        fld["value"] = value
        self._validate_and_mark_dirty()

    def update_number_field(self, section_id: str, field_id: str, value: float) -> None:
        _section, fld = self._find_field(section_id, field_id)
        if fld.get("type") != "number":
            raise EKMValidationError(f"Field {field_id!r} is not a number field")
        fld["value"] = value
        self._validate_and_mark_dirty()

    def update_measurement_field(
        self,
        section_id: str,
        field_id: str,
        value: float,
        unit: str,
        *,
        conditions: str = "",
    ) -> None:
        _section, fld = self._find_field(section_id, field_id)
        if fld.get("type") != "measurement":
            raise EKMValidationError(f"Field {field_id!r} is not a measurement field")
        payload = parse_measurement_input(str(value), unit, conditions)
        fld["value"] = payload
        self._validate_and_mark_dirty()

    def update_reference_field(
        self,
        section_id: str,
        field_id: str,
        kind: str,
        ref: str,
        *,
        sheet_path: str = "",
    ) -> None:
        _section, fld = self._find_field(section_id, field_id)
        if fld.get("type") != "reference":
            raise EKMValidationError(f"Field {field_id!r} is not a reference field")
        fld["value"] = parse_reference_input(kind, ref, sheet_path)
        self._validate_and_mark_dirty()

    def reload(self) -> None:
        self.document = load(self.project_path)
        self.dirty = False
        self.last_error = None

    def save(self) -> Path:
        self.last_error = None
        try:
            path = save(self.document, self.project_path)
        except EKMError as exc:
            self.last_error = str(exc)
            raise
        self.dirty = False
        self.document = load(path)
        return path


def editor_kind_for_field(field_type: str) -> str:
    """Backward-compatible helper."""
    return editor_kind_for_type(field_type)


def reference_kind_choices() -> list[str]:
    return sorted(KICAD_LINK_KINDS)
