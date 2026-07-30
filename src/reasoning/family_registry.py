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
class CircuitFamily:
    family_id: str
    directory: str
    label: str
    status: str = "planned"

    @property
    def path(self) -> Path:
        return _DEFAULT_MANIFEST.parent / self.directory


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
            )
        )
    return families


def get_family(family_id: str, manifest_path: Path | None = None) -> CircuitFamily:
    for family in load_families(manifest_path):
        if family.family_id == family_id:
            return family
    raise KeyError(f"Unknown circuit family: {family_id}")
