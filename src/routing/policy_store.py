"""Per-project routing policy persistence under ``kicad_ai/routing_policy.json``."""

from __future__ import annotations

import json
from pathlib import Path

from routing.types import NetClassification, NetClassificationEntry, RoutingPolicy


def routing_policy_file_path(project_path: Path | str) -> Path:
    """Return ``<project_root>/kicad_ai/routing_policy.json`` for a .kicad_pro path."""
    pro = Path(project_path).expanduser().resolve()
    return pro.parent / "kicad_ai" / "routing_policy.json"


def routing_policy_from_dict(data: dict) -> RoutingPolicy:
    """Deserialize a routing policy from JSON-compatible dict."""
    entries: list[NetClassificationEntry] = []
    raw_entries = data.get("net_classifications")
    if isinstance(raw_entries, list):
        for item in raw_entries:
            if not isinstance(item, dict):
                continue
            net_name = item.get("net_name")
            classification = item.get("classification")
            if not isinstance(net_name, str) or not net_name.strip():
                continue
            if classification not in {
                "critical_manual",
                "critical_constrained",
                "high_current",
                "power",
                "ground",
                "differential",
                "clock",
                "analog_sensitive",
                "rf",
                "sense",
                "ordinary_signal",
                "low_priority",
            }:
                continue
            entries.append(
                NetClassificationEntry(
                    net_name=net_name.strip(),
                    classification=classification,  # type: ignore[arg-type]
                    explain=str(item.get("explain") or ""),
                )
            )
    notes = data.get("notes")
    return RoutingPolicy(
        net_classifications=entries,
        notes=str(notes) if isinstance(notes, str) else "",
    )


def load_routing_policy(project_path: Path | str) -> RoutingPolicy | None:
    """Load persisted routing policy for a project, or ``None`` if absent."""
    path = routing_policy_file_path(project_path)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return routing_policy_from_dict(data)


def save_routing_policy(project_path: Path | str, policy: RoutingPolicy) -> Path:
    """Persist routing policy beside other ``kicad_ai/`` project artifacts."""
    path = routing_policy_file_path(project_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(policy.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path
