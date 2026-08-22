"""Project file fingerprints for incremental context refresh."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from context.schematic_parse import discover_schematic_paths

CONTEXT_LAYERS = ("schematic", "pcb", "bom", "erc_drc", "netlist", "image", "datasheets")

FINGERPRINT_FILENAME = "context_fingerprint.json"


def fingerprint_file_path(project_path: Path | str) -> Path:
    """Return ``<project_root>/kicad_ai/context_fingerprint.json``."""
    pro = Path(project_path).expanduser().resolve()
    return pro.parent / "kicad_ai" / FINGERPRINT_FILENAME


@dataclass
class ProjectFingerprint:
    """Per-layer file stat signatures for a KiCad project."""

    project_path: str
    layers: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"project_path": self.project_path, "layers": dict(self.layers)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectFingerprint:
        layers_raw = data.get("layers")
        layers = (
            {str(k): str(v) for k, v in layers_raw.items()}
            if isinstance(layers_raw, dict)
            else {}
        )
        return cls(
            project_path=str(data.get("project_path", "")),
            layers=layers,
        )


def _file_signature(path: Path) -> str | None:
    if not path.is_file():
        return None
    stat = path.stat()
    return f"{path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}"


def _combine_signatures(paths: list[Path]) -> str:
    parts: list[str] = []
    for path in sorted({p.resolve() for p in paths}):
        sig = _file_signature(path)
        if sig is not None:
            parts.append(sig)
    return "|".join(parts)


def _resolve_pro(project_path: Path | str) -> Path:
    path = Path(project_path).expanduser().resolve()
    if path.is_file() and path.suffix == ".kicad_pro":
        return path
    if path.is_dir():
        pros = sorted(path.glob("*.kicad_pro"))
        if pros:
            return pros[0]
    raise FileNotFoundError(f"No .kicad_pro found for {project_path}")


def compute_fingerprint(project_path: Path | str) -> ProjectFingerprint:
    """Compute per-layer fingerprints from project file mtimes/sizes."""
    pro = _resolve_pro(project_path)
    project_root = pro.parent
    schematic_paths = discover_schematic_paths(pro)
    pcb_path = pro.with_suffix(".kicad_pcb")
    manifest_path = project_root / "kicad_ai" / "artifact_manifest.json"

    layers: dict[str, str] = {
        "schematic": _combine_signatures(schematic_paths),
        "pcb": _combine_signatures([pcb_path]),
        "bom": _combine_signatures(schematic_paths),
        "erc_drc": _combine_signatures([pro, pcb_path, *schematic_paths]),
        "netlist": _combine_signatures([pro, pcb_path, *schematic_paths]),
        "image": _combine_signatures(schematic_paths[:1]),
        "datasheets": _combine_signatures([manifest_path, pro]),
    }
    return ProjectFingerprint(project_path=str(pro), layers=layers)


def dirty_layers(
    previous: ProjectFingerprint | None,
    current: ProjectFingerprint,
) -> set[str]:
    """Return layer names whose fingerprint changed since ``previous``."""
    if previous is None:
        return set(CONTEXT_LAYERS)
    dirty: set[str] = set()
    for layer in CONTEXT_LAYERS:
        if previous.layers.get(layer) != current.layers.get(layer):
            dirty.add(layer)
    return dirty


def project_changed_since(
    previous: ProjectFingerprint | None,
    current: ProjectFingerprint,
) -> bool:
    """Return True when any tracked layer fingerprint differs."""
    return bool(dirty_layers(previous, current))


def load_fingerprint(project_path: Path | str) -> ProjectFingerprint | None:
    """Load a persisted fingerprint from ``kicad_ai/context_fingerprint.json``."""
    path = fingerprint_file_path(project_path)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return ProjectFingerprint.from_dict(data)


def save_fingerprint(fingerprint: ProjectFingerprint) -> Path:
    """Persist fingerprint alongside other ``kicad_ai/`` project artifacts."""
    path = fingerprint_file_path(fingerprint.project_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fingerprint.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path
