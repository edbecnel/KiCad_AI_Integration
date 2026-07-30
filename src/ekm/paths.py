"""EKM file path resolution (host-agnostic)."""

from __future__ import annotations

from pathlib import Path

EKM_DIR_NAME = "kicad_ai"
EKM_FILENAME = "engineering_knowledge.json"


def ekm_path_for_project(project_dir: Path) -> Path:
    """Return canonical EKM path under a project directory."""
    return Path(project_dir).expanduser().resolve() / EKM_DIR_NAME / EKM_FILENAME


def resolve_ekm_path(path: Path) -> Path:
    """Resolve a path that may be a project dir or an EKM JSON file."""
    p = Path(path).expanduser().resolve()
    if p.is_dir():
        return ekm_path_for_project(p)
    return p
