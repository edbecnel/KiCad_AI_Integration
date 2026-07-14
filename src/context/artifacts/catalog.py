"""Shared artifact catalog (catalog.json)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

ArtifactType = Literal["datasheet", "lib"]
CATALOG_VERSION = 1


@dataclass
class ComponentRef:
    reference: str
    sheet_path: str
    sheet_name: str = "/"

    def to_dict(self) -> dict[str, str]:
        return {
            "reference": self.reference,
            "sheet_path": self.sheet_path,
            "sheet_name": self.sheet_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ComponentRef:
        return cls(
            reference=data["reference"],
            sheet_path=data["sheet_path"],
            sheet_name=data.get("sheet_name", "/"),
        )


@dataclass
class ProjectReference:
    project_path: str
    project_name: str
    schematics: list[str] = field(default_factory=list)
    components: list[ComponentRef] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_path": self.project_path,
            "project_name": self.project_name,
            "schematics": self.schematics,
            "components": [c.to_dict() for c in self.components],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectReference:
        return cls(
            project_path=data["project_path"],
            project_name=data["project_name"],
            schematics=list(data.get("schematics") or []),
            components=[
                ComponentRef.from_dict(c) for c in (data.get("components") or [])
            ],
        )


@dataclass
class ArtifactEntry:
    id: str
    type: ArtifactType
    part: str
    file: str
    sha256: str
    source: str
    referenced_by: list[ProjectReference] = field(default_factory=list)
    tier: str | None = None
    generated: str | None = None
    source_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "part": self.part,
            "file": self.file,
            "sha256": self.sha256,
            "source": self.source,
            "referenced_by": [r.to_dict() for r in self.referenced_by],
        }
        if self.tier is not None:
            data["tier"] = self.tier
        if self.generated is not None:
            data["generated"] = self.generated
        if self.source_url is not None:
            data["source_url"] = self.source_url
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArtifactEntry:
        return cls(
            id=data["id"],
            type=data["type"],
            part=data["part"],
            file=data["file"],
            sha256=data["sha256"],
            source=data["source"],
            referenced_by=[
                ProjectReference.from_dict(r)
                for r in (data.get("referenced_by") or [])
            ],
            tier=data.get("tier"),
            generated=data.get("generated"),
            source_url=data.get("source_url"),
        )


def generate_artifact_id(artifact_type: ArtifactType, part: str) -> str:
    prefix = "ds" if artifact_type == "datasheet" else "lib"
    slug = "".join(ch if ch.isalnum() else "-" for ch in part.upper())[:24]
    short = uuid.uuid4().hex[:6]
    return f"{prefix}-{slug}-{short}"


class Catalog:
    """CRUD for shared catalog.json."""

    def __init__(self, library_path: Path) -> None:
        self.library_path = library_path.expanduser().resolve()
        self.catalog_path = self.library_path / "catalog.json"
        self._data: dict[str, Any] | None = None

    def bootstrap(self) -> None:
        self.library_path.mkdir(parents=True, exist_ok=True)
        (self.library_path / "datasheets").mkdir(exist_ok=True)
        (self.library_path / "libs").mkdir(exist_ok=True)
        if not self.catalog_path.is_file():
            self._write(
                {
                    "version": CATALOG_VERSION,
                    "library_path": str(self.library_path),
                    "artifacts": [],
                }
            )

    def load(self) -> dict[str, Any]:
        if self._data is None:
            self.bootstrap()
            with self.catalog_path.open(encoding="utf-8") as fh:
                self._data = json.load(fh)
        return self._data

    def save(self) -> None:
        if self._data is None:
            return
        self._data["library_path"] = str(self.library_path)
        self._write(self._data)

    def _write(self, data: dict[str, Any]) -> None:
        self.library_path.mkdir(parents=True, exist_ok=True)
        with self.catalog_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        self._data = data

    @property
    def artifacts(self) -> list[ArtifactEntry]:
        data = self.load()
        return [ArtifactEntry.from_dict(a) for a in data.get("artifacts", [])]

    def get_by_id(self, artifact_id: str) -> ArtifactEntry | None:
        for entry in self.artifacts:
            if entry.id == artifact_id:
                return entry
        return None

    def get_by_sha256(self, digest: str) -> ArtifactEntry | None:
        for entry in self.artifacts:
            if entry.sha256 == digest:
                return entry
        return None

    def get_by_part(self, part: str, artifact_type: ArtifactType | None = None) -> list[ArtifactEntry]:
        part_norm = part.strip()
        results: list[ArtifactEntry] = []
        for entry in self.artifacts:
            if entry.part != part_norm:
                continue
            if artifact_type is not None and entry.type != artifact_type:
                continue
            results.append(entry)
        return results

    def get_by_source_url(self, source_url: str) -> ArtifactEntry | None:
        for entry in self.artifacts:
            if entry.source_url == source_url:
                return entry
        return None

    def add_artifact(self, entry: ArtifactEntry) -> ArtifactEntry:
        data = self.load()
        artifacts = data.setdefault("artifacts", [])
        artifacts.append(entry.to_dict())
        self.save()
        return entry

    def update_artifact(self, entry: ArtifactEntry) -> None:
        data = self.load()
        artifacts = data.get("artifacts", [])
        for idx, raw in enumerate(artifacts):
            if raw.get("id") == entry.id:
                artifacts[idx] = entry.to_dict()
                self.save()
                return
        raise KeyError(f"Artifact not found: {entry.id}")

    def upsert_reference(
        self,
        artifact_id: str,
        project_ref: ProjectReference,
        component: ComponentRef,
    ) -> None:
        entry = self.get_by_id(artifact_id)
        if entry is None:
            raise KeyError(f"Artifact not found: {artifact_id}")

        proj = None
        for ref in entry.referenced_by:
            if ref.project_path == project_ref.project_path:
                proj = ref
                break
        if proj is None:
            proj = ProjectReference(
                project_path=project_ref.project_path,
                project_name=project_ref.project_name,
                schematics=list(project_ref.schematics),
                components=[],
            )
            entry.referenced_by.append(proj)

        for sch in project_ref.schematics:
            if sch not in proj.schematics:
                proj.schematics.append(sch)

        existing = next(
            (
                c
                for c in proj.components
                if c.reference == component.reference
                and c.sheet_path == component.sheet_path
            ),
            None,
        )
        if existing is None:
            proj.components.append(component)
        else:
            existing.sheet_name = component.sheet_name

        self.update_artifact(entry)

    def remove_component_reference(
        self,
        artifact_id: str,
        project_path: str,
        component_ref: str,
        sheet_path: str,
    ) -> None:
        entry = self.get_by_id(artifact_id)
        if entry is None:
            return
        for proj in entry.referenced_by:
            if proj.project_path != project_path:
                continue
            proj.components = [
                c
                for c in proj.components
                if not (
                    c.reference == component_ref and c.sheet_path == sheet_path
                )
            ]
        entry.referenced_by = [
            p for p in entry.referenced_by if p.components or p.project_path != project_path
        ]
        entry.referenced_by = [
            p
            for p in entry.referenced_by
            if p.components or any(p.schematics)
        ]
        self.update_artifact(entry)

    def sync_project_references(
        self,
        project_path: str,
        active_components: dict[str, list[ComponentRef]],
    ) -> None:
        """Remove stale component refs for a project; active_components maps artifact_id → refs."""
        for entry in self.artifacts:
            changed = False
            for proj in entry.referenced_by:
                if proj.project_path != project_path:
                    continue
                allowed = active_components.get(entry.id, [])
                allowed_keys = {
                    (c.reference, c.sheet_path) for c in allowed
                }
                new_components = [
                    c
                    for c in proj.components
                    if (c.reference, c.sheet_path) in allowed_keys
                ]
                if len(new_components) != len(proj.components):
                    proj.components = new_components
                    changed = True
            if changed:
                entry.referenced_by = [p for p in entry.referenced_by if p.components]
                self.update_artifact(entry)

    def can_delete(self, artifact_id: str) -> bool:
        entry = self.get_by_id(artifact_id)
        if entry is None:
            return True
        return len(entry.referenced_by) == 0
