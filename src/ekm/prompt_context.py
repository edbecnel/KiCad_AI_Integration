"""Load project EKM for AERF prompt assembly (learning loop L1)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ekm.io import load
from ekm.model import EKMDocument
from ekm.paths import resolve_ekm_path


@dataclass(frozen=True)
class EKMPromptBundle:
    """EKM content and family hint for AERF orchestration."""

    sections: dict[str, Any]
    family_id: str | None
    ekm_path: Path | None


def _project_dir_from_path(project_path: Path | str) -> Path:
    path = Path(project_path).expanduser().resolve()
    if path.suffix == ".kicad_pro":
        return path.parent
    return path


def extract_ekm_family_id(doc: EKMDocument) -> str | None:
    """Read persisted AERF family id from EKM circuit_overview."""
    for section in doc.sections:
        if section.get("id") != "circuit_overview":
            continue
        for field in section.get("fields") or []:
            if not isinstance(field, dict):
                continue
            field_id = field.get("id")
            if field_id == "aerf_family_id":
                value = field.get("value")
                if isinstance(value, str) and value.strip():
                    return value.strip()
            if field_id == "aerf_stage_0_determinations":
                raw = field.get("value")
                if not isinstance(raw, str):
                    continue
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(data, dict):
                    family_id = data.get("family_id")
                    if isinstance(family_id, str) and family_id.strip():
                        return family_id.strip()
    return None


def load_ekm_sections_for_prompt(project_path: Path | str) -> dict[str, Any]:
    """Build a compact EKM dict for ``<engineering_knowledge>`` prompts."""
    project_dir = _project_dir_from_path(project_path)
    ekm_path = resolve_ekm_path(project_dir)
    if not ekm_path.is_file():
        return {}
    try:
        doc = load(project_dir)
    except OSError:
        return {}

    sections_out: dict[str, Any] = {}
    for section in doc.sections:
        if not isinstance(section, dict):
            continue
        section_id = section.get("id")
        if not section_id:
            continue
        fields_out: dict[str, Any] = {}
        for field in section.get("fields") or []:
            if not isinstance(field, dict):
                continue
            fid = field.get("id")
            if not fid:
                continue
            fields_out[fid] = {
                "label": field.get("label"),
                "value": field.get("value"),
                "type": field.get("type"),
            }
        sections_out[str(section_id)] = {
            "title": section.get("title"),
            "fields": fields_out,
        }
    return sections_out


def load_ekm_prompt_bundle(project_path: Path | str) -> EKMPromptBundle:
    """Load EKM sections and family hint when the project file exists."""
    project_dir = _project_dir_from_path(project_path)
    ekm_path = resolve_ekm_path(project_dir)
    if not ekm_path.is_file():
        return EKMPromptBundle(sections={}, family_id=None, ekm_path=None)
    try:
        doc = load(project_dir)
    except OSError:
        return EKMPromptBundle(sections={}, family_id=None, ekm_path=ekm_path)

    return EKMPromptBundle(
        sections=load_ekm_sections_for_prompt(project_path),
        family_id=extract_ekm_family_id(doc),
        ekm_path=ekm_path,
    )
