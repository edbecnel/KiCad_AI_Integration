"""EKM document model (mirrors ekm_schema_v1.json primitives)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SUPPORTED_SCHEMA_VERSION = "1.0.0"
FIELD_TYPES = frozenset(
    {"text", "number", "enum", "reference", "measurement", "attachment"}
)
KICAD_LINK_KINDS = frozenset({"component", "net", "symbol", "sheet"})


@dataclass
class EKMDocument:
    schema_version: str
    sections: list[dict[str, Any]] = field(default_factory=list)
    project_path: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "sections": self.sections,
        }
        if self.project_path is not None:
            data["project_path"] = self.project_path
        if self.updated_at is not None:
            data["updated_at"] = self.updated_at
        return data

    @classmethod
    def empty(cls, *, project_path: str | None = None) -> EKMDocument:
        return cls(
            schema_version=SUPPORTED_SCHEMA_VERSION,
            sections=[],
            project_path=project_path,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EKMDocument:
        return cls(
            schema_version=str(data["schema_version"]),
            sections=list(data.get("sections") or []),
            project_path=data.get("project_path"),
            updated_at=data.get("updated_at"),
        )
