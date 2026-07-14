"""Extract net labels and schematic connectivity hints from .kicad_sch files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class NetLabel:
    """A local or global net label on a schematic sheet."""

    name: str
    sheet_path: str
    kind: str  # label, global_label, hierarchical_label


_LABEL_PATTERN = re.compile(
    r"\((label|global_label|hierarchical_label)\s+\"([^\"]*)\"",
)


def parse_schematic_labels(schematic_path: Path) -> list[NetLabel]:
    """Parse net labels from a single .kicad_sch file."""
    content = schematic_path.expanduser().read_text(encoding="utf-8")
    sheet_path = schematic_path.name
    labels: list[NetLabel] = []
    for match in _LABEL_PATTERN.finditer(content):
        labels.append(
            NetLabel(
                name=match.group(2),
                sheet_path=sheet_path,
                kind=match.group(1),
            )
        )
    return labels


def parse_project_labels(
    project_root: Path,
    schematic_paths: list[Path],
) -> list[NetLabel]:
    """Parse labels from all given schematic files."""
    all_labels: list[NetLabel] = []
    for sch in schematic_paths:
        resolved = sch if sch.is_absolute() else project_root / sch
        if resolved.is_file():
            all_labels.extend(parse_schematic_labels(resolved))
    return all_labels


def connectivity_summary(labels: list[NetLabel]) -> dict[str, object]:
    """Compact connectivity summary for prompts."""
    unique_names = sorted({label.name for label in labels if label.name})
    return {
        "label_count": len(labels),
        "unique_net_names": unique_names,
        "labels": [
            {"name": label.name, "sheet": label.sheet_path, "kind": label.kind}
            for label in labels
        ],
    }
