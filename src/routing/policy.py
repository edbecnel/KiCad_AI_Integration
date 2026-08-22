"""Routing policy helpers (Phase 3). Persistence mechanism TBD."""

from __future__ import annotations

from routing.types import (
    NetClassification,
    NetClassificationEntry,
    RoutingExclusions,
    RoutingPolicy,
)


def build_exclusions_from_policy(policy: RoutingPolicy) -> RoutingExclusions:
    """Derive routing exclusions from structured policy classifications."""
    excluded_nets = policy.excluded_nets()
    excluded_classes: list[str] = []
    for entry in policy.net_classifications:
        if entry.classification in ("power", "ground"):
            excluded_classes.append(entry.net_name)
    return RoutingExclusions(
        excluded_nets=sorted(set(excluded_nets)),
        excluded_net_classes=sorted(set(excluded_classes)),
    )


def classify_net(
    net_name: str,
    classification: NetClassification,
    *,
    explain: str = "",
) -> NetClassificationEntry:
    return NetClassificationEntry(
        net_name=net_name,
        classification=classification,
        explain=explain,
    )


def explain_exclusion(entry: NetClassificationEntry) -> str:
    """Return human-readable explanation for a net exclusion."""
    if entry.explain:
        return entry.explain
    defaults = {
        "critical_manual": f"Net {entry.net_name} requires manual routing.",
        "high_current": f"Net {entry.net_name} is high-current and needs wide copper or pour.",
        "differential": f"Net {entry.net_name} is part of a differential pair.",
        "clock": f"Net {entry.net_name} is a clock line requiring short, isolated routing.",
        "analog_sensitive": f"Net {entry.net_name} is analog-sensitive.",
        "sense": f"Net {entry.net_name} is a sense line (e.g. Kelvin connection).",
    }
    return defaults.get(
        entry.classification,
        f"Net {entry.net_name} excluded from automatic routing ({entry.classification}).",
    )
