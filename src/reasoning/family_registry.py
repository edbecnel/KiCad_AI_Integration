"""Circuit family registry (repo + user library manifest merge)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from utils.config import AppConfig, load_config

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_MANIFEST = (
    _REPO_ROOT
    / "docs"
    / "Engineering_Knowledge"
    / "Circuit_Families"
    / "families.json"
)
DEFAULT_LEARNING_LIBRARY_SUBDIR = "circuit_families"


@dataclass(frozen=True)
class FamilyRecognition:
    symbol_lib_patterns: tuple[str, ...] = ()
    net_keywords: tuple[str, ...] = ()
    min_score: int = 1


@dataclass(frozen=True)
class CircuitFamily:
    family_id: str
    directory: str
    label: str
    status: str = "planned"
    recognition: FamilyRecognition | None = None
    families_root: Path | None = None

    @property
    def path(self) -> Path:
        root = self.families_root or _DEFAULT_MANIFEST.parent
        return root / self.directory


def _parse_recognition(entry: dict) -> FamilyRecognition | None:
    raw = entry.get("recognition")
    if not raw or not isinstance(raw, dict):
        return None
    patterns = tuple(str(p) for p in raw.get("symbol_lib_patterns") or ())
    keywords = tuple(str(k) for k in raw.get("net_keywords") or ())
    min_score = int(raw.get("min_score") or 1)
    if not patterns and not keywords:
        return None
    return FamilyRecognition(
        symbol_lib_patterns=patterns,
        net_keywords=keywords,
        min_score=min_score,
    )


def _parse_manifest(path: Path, families_root: Path) -> list[CircuitFamily]:
    data = json.loads(path.read_text(encoding="utf-8"))
    families: list[CircuitFamily] = []
    for entry in data.get("families") or []:
        families.append(
            CircuitFamily(
                family_id=str(entry["family_id"]),
                directory=str(entry["directory"]),
                label=str(entry.get("label") or entry["family_id"]),
                status=str(entry.get("status") or "planned"),
                recognition=_parse_recognition(entry),
                families_root=families_root,
            )
        )
    return families


def library_circuit_families_root(
    library_path: Path | None = None,
    *,
    library_subdir: str = DEFAULT_LEARNING_LIBRARY_SUBDIR,
    config: AppConfig | None = None,
) -> Path | None:
    """Return ``<artifact_library>/circuit_families`` when configured."""
    cfg = config or load_config()
    base = library_path or cfg.artifact_library_path
    root = Path(base).expanduser() / library_subdir
    return root if root.is_dir() or (root / "families.json").is_file() else None


def load_families(
    manifest_path: Path | None = None,
    *,
    library_path: Path | None = None,
    library_subdir: str = DEFAULT_LEARNING_LIBRARY_SUBDIR,
    config: AppConfig | None = None,
) -> list[CircuitFamily]:
    """Merge repo manifest with user library manifest (library wins on id)."""
    cfg = config or load_config()
    merged: dict[str, CircuitFamily] = {}

    repo_path = manifest_path or _DEFAULT_MANIFEST
    if repo_path.is_file():
        for family in _parse_manifest(repo_path, repo_path.parent):
            merged[family.family_id] = family

    lib_base = library_path or cfg.artifact_library_path
    lib_root = Path(lib_base).expanduser() / library_subdir
    lib_manifest = lib_root / "families.json"
    if lib_manifest.is_file():
        for family in _parse_manifest(lib_manifest, lib_root):
            merged[family.family_id] = family

    return list(merged.values())


def get_family(
    family_id: str,
    manifest_path: Path | None = None,
    *,
    library_path: Path | None = None,
    library_subdir: str = DEFAULT_LEARNING_LIBRARY_SUBDIR,
    config: AppConfig | None = None,
) -> CircuitFamily:
    for family in load_families(
        manifest_path,
        library_path=library_path,
        library_subdir=library_subdir,
        config=config,
    ):
        if family.family_id == family_id:
            return family
    raise KeyError(f"Unknown circuit family: {family_id}")
