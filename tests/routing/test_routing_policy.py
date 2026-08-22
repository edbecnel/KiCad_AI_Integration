"""Tests for routing policy helpers."""

from __future__ import annotations

from routing.policy import build_exclusions_from_policy, classify_net, explain_exclusion
from routing.types import RoutingPolicy


def test_build_exclusions_from_policy() -> None:
    policy = RoutingPolicy(
        net_classifications=[
            classify_net("MOTOR_OUT", "high_current", explain="20 A path"),
            classify_net("SPI_MOSI", "ordinary_signal"),
        ]
    )
    exclusions = build_exclusions_from_policy(policy)
    assert "MOTOR_OUT" in exclusions.excluded_nets
    assert "SPI_MOSI" not in exclusions.excluded_nets


def test_explain_exclusion_uses_custom_text() -> None:
    entry = classify_net("XTAL_IN", "clock", explain="Oscillator network")
    assert explain_exclusion(entry) == "Oscillator network"


def test_explain_exclusion_default() -> None:
    entry = classify_net("CLK", "clock")
    assert "CLK" in explain_exclusion(entry)
