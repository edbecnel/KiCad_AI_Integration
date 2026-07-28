"""Artifact file operations, deduplication, and registration."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from utils.hashing import sha256_file

from .catalog import (
    ArtifactEntry,
    ArtifactType,
    Catalog,
    ComponentRef,
    ProjectReference,
    generate_artifact_id,
)
from .manifest import Manifest, ManifestComponentLink
from .ai_discovery_log import AiDiscoveryLog
from .url_fetch_log import UrlFetchLog


@dataclass
class ProjectContextInfo:
    """Minimal project identity for artifact registration."""

    project_pro_path: Path
    schematic_paths: list[Path]

    @property
    def project_path(self) -> str:
        return str(self.project_pro_path.expanduser().resolve())

    @property
    def project_name(self) -> str:
        return self.project_pro_path.stem

    @property
    def project_root(self) -> Path:
        return self.project_pro_path.expanduser().resolve().parent


class ArtifactDeletionError(RuntimeError):
    """Raised when attempting to delete a referenced shared artifact."""


class ArtifactStore:
    """Two-layer artifact library: shared catalog + per-project manifest."""

    def __init__(self, library_path: Path) -> None:
        self.library_path = library_path.expanduser().resolve()
        self.catalog = Catalog(self.library_path)
        self.url_fetch_log = UrlFetchLog(self.library_path)
        self.ai_discovery_log = AiDiscoveryLog(self.library_path)

    def bootstrap(self) -> None:
        self.catalog.bootstrap()
        self.url_fetch_log.bootstrap()
        self.ai_discovery_log.bootstrap()
        (self.library_path / "datasheets").mkdir(parents=True, exist_ok=True)
        (self.library_path / "libs").mkdir(parents=True, exist_ok=True)

    def scan_datasheets_folder(self) -> int:
        """
        Register PDFs already in ``datasheets/`` that are not in the catalog.

        Returns the number of new catalog entries added.
        """
        self.bootstrap()
        folder = self.library_path / "datasheets"
        if not folder.is_dir():
            return 0
        added = 0
        for pdf in sorted(folder.glob("*.pdf")):
            part = pdf.stem
            if self.catalog.get_by_part(part, "datasheet"):
                continue
            digest = sha256_file(pdf)
            if self.catalog.get_by_sha256(digest) is not None:
                continue
            relative = self._relative_artifact_path("datasheet", pdf.name)
            entry = ArtifactEntry(
                id=generate_artifact_id("datasheet", part),
                type="datasheet",
                part=part,
                file=relative,
                sha256=digest,
                source="folder_scan",
            )
            self.catalog.add_artifact(entry)
            added += 1
        return added

    def bootstrap_project(self, project_pro_path: Path) -> Path:
        root = project_pro_path.expanduser().resolve().parent
        exports = root / "kicad_ai" / "exports"
        exports.mkdir(parents=True, exist_ok=True)
        manifest = Manifest.load(project_pro_path)
        if not manifest.manifest_path.is_file():
            manifest.save()
        return exports

    def _relative_artifact_path(self, artifact_type: ArtifactType, filename: str) -> str:
        subdir = "datasheets" if artifact_type == "datasheet" else "libs"
        return f"{subdir}/{filename}"

    def _dest_path(self, relative_file: str) -> Path:
        return self.library_path / relative_file

    def register_datasheet(
        self,
        source_path: Path,
        part: str,
        source: str,
        project: ProjectContextInfo,
        component_ref: ComponentRef | None = None,
        *,
        source_url: str | None = None,
    ) -> ArtifactEntry:
        return self._register_file(
            source_path=source_path,
            part=part,
            artifact_type="datasheet",
            source=source,
            project=project,
            component_ref=component_ref,
            dest_name=f"{self._safe_part_filename(part)}.pdf",
            source_url=source_url,
        )

    def register_lib(
        self,
        source_path: Path,
        part: str,
        source: str,
        project: ProjectContextInfo,
        component_ref: ComponentRef | None = None,
        tier: str | None = None,
    ) -> ArtifactEntry:
        entry = self._register_file(
            source_path=source_path,
            part=part,
            artifact_type="lib",
            source=source,
            project=project,
            component_ref=component_ref,
            dest_name=f"{self._safe_part_filename(part)}.lib",
        )
        if tier:
            entry.tier = tier
            from datetime import datetime, timezone

            entry.generated = datetime.now(timezone.utc).isoformat()
            self.catalog.update_artifact(entry)
        return entry

    def _safe_part_filename(self, part: str) -> str:
        cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in part.strip())
        return cleaned or "unknown_part"

    def _register_file(
        self,
        source_path: Path,
        part: str,
        artifact_type: ArtifactType,
        source: str,
        project: ProjectContextInfo,
        component_ref: ComponentRef | None,
        dest_name: str,
        source_url: str | None = None,
    ) -> ArtifactEntry:
        self.bootstrap()
        self.bootstrap_project(project.project_pro_path)

        source_path = source_path.expanduser().resolve()
        if not source_path.is_file():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        digest = sha256_file(source_path)
        existing = self.catalog.get_by_sha256(digest)
        if existing is not None:
            if component_ref is not None:
                self.link_existing(
                    existing.id, project, component_ref, part=part.strip()
                )
            return existing

        relative = self._relative_artifact_path(artifact_type, dest_name)
        dest = self._dest_path(relative)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if source_path.resolve() != dest.resolve():
            shutil.copy2(source_path, dest)

        entry = ArtifactEntry(
            id=generate_artifact_id(artifact_type, part),
            type=artifact_type,
            part=part.strip(),
            file=relative,
            sha256=digest,
            source=source,
            source_url=source_url,
        )
        self.catalog.add_artifact(entry)

        if component_ref is not None:
            self.link_existing(entry.id, project, component_ref, part=part.strip())
        return entry

    def link_existing(
        self,
        artifact_id: str,
        project: ProjectContextInfo,
        component_ref: ComponentRef,
        *,
        part: str | None = None,
        manifest: Manifest | None = None,
        save_manifest: bool = True,
    ) -> ArtifactEntry:
        entry = self.catalog.get_by_id(artifact_id)
        if entry is None:
            raise KeyError(f"Artifact not found: {artifact_id}")

        project_ref = ProjectReference(
            project_path=project.project_path,
            project_name=project.project_name,
            schematics=[str(p.name) for p in project.schematic_paths],
            components=[],
        )
        self.catalog.upsert_reference(artifact_id, project_ref, component_ref)

        manifest_obj = manifest if manifest is not None else Manifest.load(project.project_pro_path)
        manifest_part = (part or entry.part).strip()
        manifest_obj.upsert_link(
            artifact_id=artifact_id,
            part=manifest_part,
            component=ManifestComponentLink(
                reference=component_ref.reference,
                sheet_path=component_ref.sheet_path,
            ),
        )
        if save_manifest:
            manifest_obj.save()
        return entry

    def get_by_part(self, part: str, artifact_type: ArtifactType | None = None) -> list[ArtifactEntry]:
        return self.catalog.get_by_part(part, artifact_type)

    def resolve_local_path(self, artifact_id: str) -> Path | None:
        entry = self.catalog.get_by_id(artifact_id)
        if entry is None:
            return None
        path = self._dest_path(entry.file)
        return path if path.is_file() else None

    def delete_artifact(self, artifact_id: str) -> None:
        if not self.catalog.can_delete(artifact_id):
            raise ArtifactDeletionError(
                f"Cannot delete {artifact_id}: still referenced by projects"
            )
        entry = self.catalog.get_by_id(artifact_id)
        if entry is None:
            return
        file_path = self._dest_path(entry.file)
        if file_path.is_file():
            file_path.unlink()
        data = self.catalog.load()
        data["artifacts"] = [
            a for a in data.get("artifacts", []) if a.get("id") != artifact_id
        ]
        self.catalog.save()
