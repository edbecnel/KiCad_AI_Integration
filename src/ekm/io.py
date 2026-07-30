"""EKM load/save with atomic writes."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ekm.errors import EKMIOError, EKMValidationError
from ekm.model import EKMDocument
from ekm.paths import ekm_path_for_project, resolve_ekm_path
from ekm.validate import validate_document_data


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json_file(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EKMIOError(f"Cannot read {path}: {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EKMValidationError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise EKMValidationError(f"EKM root must be an object in {path}")
    return data


def load(path: Path) -> EKMDocument:
    """Load and validate an EKM document from a file or project directory."""
    ekm_path = resolve_ekm_path(path)
    if not ekm_path.is_file():
        raise EKMIOError(f"EKM file not found: {ekm_path}")
    return validate_document_data(load_json_file(ekm_path))


def save(doc: EKMDocument, path: Path, *, atomic: bool = True) -> Path:
    """Validate and save an EKM document atomically."""
    ekm_path = resolve_ekm_path(path)
    validate_document_data(doc.to_dict())
    doc.updated_at = _utc_now_iso()
    ekm_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(doc.to_dict(), indent=2, ensure_ascii=False) + "\n"
    if atomic:
        tmp = ekm_path.with_suffix(ekm_path.suffix + ".tmp")
        try:
            tmp.write_text(payload, encoding="utf-8")
            os.replace(tmp, ekm_path)
        except OSError as exc:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass
            raise EKMIOError(f"Cannot write {ekm_path}: {exc}") from exc
    else:
        try:
            ekm_path.write_text(payload, encoding="utf-8")
        except OSError as exc:
            raise EKMIOError(f"Cannot write {ekm_path}: {exc}") from exc
    return ekm_path


def init_empty(project_dir: Path, *, project_path: str | None = None) -> Path:
    """Create an empty EKM file under project_dir/kicad_ai/."""
    doc = EKMDocument.empty(project_path=project_path)
    return save(doc, ekm_path_for_project(project_dir))


def document_summary(doc: EKMDocument) -> dict[str, Any]:
    """Summary for CLI show command."""
    field_type_counts: dict[str, int] = {}
    for section in doc.sections:
        for fld in section.get("fields") or []:
            if isinstance(fld, dict):
                ftype = fld.get("type")
                if isinstance(ftype, str):
                    field_type_counts[ftype] = field_type_counts.get(ftype, 0) + 1
    return {
        "schema_version": doc.schema_version,
        "section_count": len(doc.sections),
        "field_type_counts": field_type_counts,
        "project_path": doc.project_path,
        "updated_at": doc.updated_at,
    }
