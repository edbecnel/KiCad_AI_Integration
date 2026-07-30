"""Load circuit-family KB markdown excerpts by AERF stage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reasoning.family_registry import CircuitFamily, get_family
from reasoning.stages import AERFStage, get_stage


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
) -> KBExcerpt:
    family = get_family(family_id)
    stage = get_stage(stage_id)
    root = families_root or family.path.parent
    family_dir = root / family.directory
    stage_path = family_dir / stage.filename
    if not stage_path.is_file():
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
) -> list[Path]:
    family = get_family(family_id)
    root = families_root or family.path.parent
    family_dir = root / family.directory
    if not family_dir.is_dir():
        return []
    return sorted(family_dir.glob("*.md"))
