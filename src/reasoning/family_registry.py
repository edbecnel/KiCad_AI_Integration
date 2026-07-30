"""Circuit family registry (manifest-driven)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_MANIFEST = (
    _REPO_ROOT
    / "docs"
    / "Engineering_Knowledge"
    / "Circuit_Families"
    / "families.json"
)


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

    @property
    def path(self) -> Path:
        return _DEFAULT_MANIFEST.parent / self.directory


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


def load_families(manifest_path: Path | None = None) -> list[CircuitFamily]:
    path = manifest_path or _DEFAULT_MANIFEST
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
            )
        )
    return families


def get_family(family_id: str, manifest_path: Path | None = None) -> CircuitFamily:
    for family in load_families(manifest_path):
        if family.family_id == family_id:
            return family
    raise KeyError(f"Unknown circuit family: {family_id}")
