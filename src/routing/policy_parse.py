"""Parse AI-generated routing policy JSON into ``RoutingPolicy``."""

from __future__ import annotations

import json
import re
from typing import Any

from routing.policy_store import routing_policy_from_dict
from routing.types import RoutingPolicy

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def _extract_json_object(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None
    fence = _JSON_FENCE_RE.search(stripped)
    if fence:
        stripped = fence.group(1).strip()
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            data = json.loads(stripped[start : end + 1])
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, dict) else None


def parse_routing_policy_json(text: str) -> RoutingPolicy:
    """Parse provider response text into a structured routing policy.

    Raises ``ValueError`` when no valid policy object can be extracted.
    """
    data = _extract_json_object(text)
    if data is None:
        raise ValueError("Response did not contain valid routing policy JSON.")
    if "net_classifications" not in data:
        raise ValueError("Routing policy JSON must include net_classifications.")
    if not isinstance(data["net_classifications"], list):
        raise ValueError("net_classifications must be a list.")
    policy = routing_policy_from_dict(data)
    if not policy.net_classifications and not policy.notes:
        raise ValueError("Routing policy contained no net classifications or notes.")
    return policy
