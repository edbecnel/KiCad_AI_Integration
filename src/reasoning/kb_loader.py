"""Load circuit-family KB markdown excerpts by AERF stage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reasoning.family_registry import (
    DEFAULT_LEARNING_LIBRARY_SUBDIR,
    get_family,
    library_circuit_families_root,
)
from reasoning.stages import AERFStage, get_stage
from utils.config import AppConfig, load_config


class KBLoadError(Exception):
    """KB file missing or unreadable."""


@dataclass(frozen=True)
class KBExcerpt:
    family_id: str
    stage: AERFStage
    path: Path
    content: str


def load_stage_excerpt(
    family_id: str,
    stage_id: int,
    *,
    families_root: Path | None = None,
    library_path: Path | None = None,
    library_subdir: str = DEFAULT_LEARNING_LIBRARY_SUBDIR,
    config: AppConfig | None = None,
) -> KBExcerpt:
    cfg = config or load_config()
    family = get_family(
        family_id,
        library_path=library_path or cfg.artifact_library_path,
        library_subdir=library_subdir,
        config=cfg,
    )
    stage = get_stage(stage_id)
    if families_root is not None:
        family_dir = families_root / family.directory
    else:
        family_dir = family.path
    stage_path = family_dir / stage.filename
    if not stage_path.is_file():
        if family_id != "generic":
            return load_stage_excerpt(
                "generic",
                stage_id,
                library_path=library_path,
                library_subdir=library_subdir,
                config=cfg,
            )
        raise KBLoadError(f"KB stage file not found: {stage_path}")
    content = stage_path.read_text(encoding="utf-8")
    return KBExcerpt(
        family_id=family_id,
        stage=stage,
        path=stage_path,
        content=content,
    )


def list_available_stage_files(
    family_id: str,
    *,
    families_root: Path | None = None,
    library_path: Path | None = None,
    library_subdir: str = DEFAULT_LEARNING_LIBRARY_SUBDIR,
    config: AppConfig | None = None,
) -> list[Path]:
    cfg = config or load_config()
    family = get_family(
        family_id,
        library_path=library_path or cfg.artifact_library_path,
        library_subdir=library_subdir,
        config=cfg,
    )
    if families_root is not None:
        family_dir = families_root / family.directory
    else:
        family_dir = family.path
    if not family_dir.is_dir():
        return []
    return sorted(family_dir.glob("*.md"))
