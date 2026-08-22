"""Tests for routing inference orchestration."""

from __future__ import annotations

from pathlib import Path

from inference.routing import build_routing_request, run_routing
from routing.policy import classify_net
from routing.types import RoutingPolicy
from utils.config import AppConfig


def test_build_routing_request(blocking_oscillator_pro: Path) -> None:
    policy = RoutingPolicy(
        net_classifications=[classify_net("GND", "ground")]
    )
    request = build_routing_request(
        blocking_oscillator_pro,
        policy=policy,
        config=AppConfig(routing_timeout_sec=120),
    )
    assert request.board_reference.project_path == blocking_oscillator_pro.resolve()
    assert request.execution_options.timeout_sec == 120


def test_run_routing_disabled(blocking_oscillator_pro: Path) -> None:
    request = build_routing_request(
        blocking_oscillator_pro,
        config=AppConfig(routing_enabled=False),
    )
    result = run_routing(request, config=AppConfig(routing_enabled=False))
    assert result.success is False
    assert "disabled" in result.errors[0].lower()
