"""Optional E2E routing test (requires Freerouting + pcbnew)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from inference.routing import (
    build_routing_request,
    get_routing_panel_context,
    run_routing,
)
from routing.policy import classify_net
from routing.policy_store import load_routing_policy, save_routing_policy
from routing.types import RoutingPolicy
from utils.config import AppConfig


def test_routing_panel_loads_persisted_policy(blocking_oscillator_pro: Path) -> None:
    policy = RoutingPolicy(
        net_classifications=[classify_net("GND", "ground", explain="Pour only")],
        notes="Persisted test policy",
    )
    save_routing_policy(blocking_oscillator_pro, policy)
    panel = get_routing_panel_context(blocking_oscillator_pro)
    assert panel.policy.notes == "Persisted test policy"
    assert load_routing_policy(blocking_oscillator_pro) is not None


def test_build_routing_request_uses_persisted_policy(blocking_oscillator_pro: Path) -> None:
    save_routing_policy(
        blocking_oscillator_pro,
        RoutingPolicy(
            net_classifications=[classify_net("HV", "critical_manual")],
        ),
    )
    request = build_routing_request(
        blocking_oscillator_pro,
        config=AppConfig(routing_enabled=True),
    )
    assert "HV" in request.routing_policy.excluded_nets()


@pytest.mark.kicad
def test_routing_e2e_when_freerouting_available(blocking_oscillator_pro: Path) -> None:
    if not os.environ.get("FREEROUTING_JAR") and not os.environ.get("FREEROUTING_CLI"):
        pytest.skip("FREEROUTING_JAR or FREEROUTING_CLI not set")

    try:
        import pcbnew  # noqa: F401
    except ImportError:
        pytest.skip("pcbnew not available")

    if pcbnew.GetBoard() is None:  # type: ignore[name-defined]
        pytest.skip("No open pcbnew board for E2E routing")

    cfg = AppConfig(routing_enabled=True)
    request = build_routing_request(blocking_oscillator_pro, config=cfg)
    result = run_routing(request, config=cfg)
    assert result.success or result.errors
    if result.success:
        summary = result.to_dict()
        assert "candidate_pcb_path" in summary
        assert summary.get("candidate_pcb_path")
