"""Tests for routing policy persistence."""

from __future__ import annotations

import json
from pathlib import Path

from routing.policy import classify_net
from routing.policy_store import (
    load_routing_policy,
    routing_policy_file_path,
    routing_policy_from_dict,
    save_routing_policy,
)
from routing.types import RoutingPolicy


def test_routing_policy_file_path(blocking_oscillator_pro: Path) -> None:
    assert routing_policy_file_path(blocking_oscillator_pro) == (
        blocking_oscillator_pro.parent / "kicad_ai" / "routing_policy.json"
    )


def test_save_and_load_routing_policy(blocking_oscillator_pro: Path) -> None:
    policy = RoutingPolicy(
        net_classifications=[
            classify_net("MOTOR_OUT", "high_current", explain="20 A path"),
        ],
        notes="Exclude high-current nets from autoroute.",
    )
    path = save_routing_policy(blocking_oscillator_pro, policy)
    assert path.is_file()
    loaded = load_routing_policy(blocking_oscillator_pro)
    assert loaded is not None
    assert loaded.notes == policy.notes
    assert len(loaded.net_classifications) == 1
    assert loaded.net_classifications[0].net_name == "MOTOR_OUT"


def test_routing_policy_from_dict_skips_invalid_entries() -> None:
    policy = routing_policy_from_dict(
        {
            "net_classifications": [
                {"net_name": "CLK", "classification": "clock", "explain": "Oscillator"},
                {"net_name": "", "classification": "clock"},
                {"net_name": "BAD", "classification": "not_a_class"},
            ],
            "notes": "test",
        }
    )
    assert len(policy.net_classifications) == 1
    assert policy.net_classifications[0].net_name == "CLK"
