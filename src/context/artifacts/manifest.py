"""Per-project artifact manifest (project_manifest.json)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ManifestComponentLink:
    reference: str
    sheet_path: str

    def to_dict(self) -> dict[str, str]:
        return {"reference": self.reference, "sheet_path": self.sheet_path}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ManifestComponentLink:
        return cls(reference=data["reference"], sheet_path=data["sheet_path"])


@dataclass
class ManifestLink:
    artifact_id: str
    part: str
    components: list[ManifestComponentLink] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "part": self.part,
            "components": [c.to_dict() for c in self.components],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ManifestLink:
        return cls(
            artifact_id=data["artifact_id"],
            part=data["part"],
            components=[
                ManifestComponentLink.from_dict(c)
                for c in (data.get("components") or [])
            ],
        )


@dataclass
class Manifest:
    project_path: str
    project_name: str
    links: list[ManifestLink] = field(default_factory=list)

    @property
    def manifest_path(self) -> Path:
        pro_path = Path(self.project_path).expanduser().resolve()
        return pro_path.parent / "kicad_ai" / "project_manifest.json"

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_path": self.project_path,
            "project_name": self.project_name,
            "links": [link.to_dict() for link in self.links],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Manifest:
        return cls(
            project_path=data["project_path"],
            project_name=data["project_name"],
            links=[ManifestLink.from_dict(l) for l in (data.get("links") or [])],
        )

    @classmethod
    def load(cls, project_pro_path: Path) -> Manifest:
        pro_path = project_pro_path.expanduser().resolve()
        manifest_path = pro_path.parent / "kicad_ai" / "project_manifest.json"
        if manifest_path.is_file():
            with manifest_path.open(encoding="utf-8") as fh:
                return cls.from_dict(json.load(fh))
        return cls(
            project_path=str(pro_path),
            project_name=pro_path.stem,
            links=[],
        )

    def save(self) -> Path:
        path = self.manifest_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
            fh.write("\n")
        return path

    def get_link(self, artifact_id: str, part: str | None = None) -> ManifestLink | None:
        for link in self.links:
            if link.artifact_id != artifact_id:
                continue
            if part is not None and link.part != part:
                continue
            return link
        return None

    def get_links_for_part(self, part: str) -> list[ManifestLink]:
        return [link for link in self.links if link.part == part]

    def upsert_link(
        self,
        artifact_id: str,
        part: str,
        component: ManifestComponentLink,
    ) -> None:
        link = self.get_link(artifact_id, part)
        if link is None:
            link = ManifestLink(artifact_id=artifact_id, part=part, components=[])
            self.links.append(link)
        existing = next(
            (
                c
                for c in link.components
                if c.reference == component.reference
                and c.sheet_path == component.sheet_path
            ),
            None,
        )
        if existing is None:
            link.components.append(component)

    def remove_stale_components(
        self,
        active_keys: set[tuple[str, str, str]],
    ) -> None:
        """active_keys: (artifact_id, reference, sheet_path)."""
        for link in self.links:
            link.components = [
                c
                for c in link.components
                if (link.artifact_id, c.reference, c.sheet_path) in active_keys
            ]
        self.links = [link for link in self.links if link.components]
