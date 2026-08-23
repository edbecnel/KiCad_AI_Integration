"""Tests for routing candidate persistence (Phase 5)."""

from __future__ import annotations

from pathlib import Path

from routing.candidates import (
    append_routing_candidate,
    compare_routing_candidates,
    load_routing_candidates,
    record_from_routing_run,
)
from routing.policy import classify_net
from routing.types import RoutingPolicy, RoutingQualityReport, RoutingResult


def test_append_and_compare_routing_candidates(blocking_oscillator_pro: Path) -> None:
    policy = RoutingPolicy(
        net_classifications=[classify_net("GND", "ground")],
        notes="test",
    )
    record_a = record_from_routing_run(
        RoutingResult(
            success=True,
            routed_net_count=10,
            unrouted_net_count=2,
            checkpoint_id="20260824T000000Z",
            candidate_pcb_path=Path("/tmp/candidate.kicad_pcb"),
        ),
        policy=policy,
        quality=RoutingQualityReport(routed_percentage=83.3, via_count=5),
    )
    record_b = record_from_routing_run(
        RoutingResult(
            success=True,
            routed_net_count=12,
            unrouted_net_count=0,
            checkpoint_id="20260824T000001Z",
            candidate_pcb_path=Path("/tmp/candidate2.kicad_pcb"),
        ),
        policy=policy,
        quality={"routed_percentage": 100.0, "via_count": 3},
    )
    append_routing_candidate(blocking_oscillator_pro, record_a)
    append_routing_candidate(blocking_oscillator_pro, record_b)
    loaded = load_routing_candidates(blocking_oscillator_pro)
    assert len(loaded) == 2
    comparison = compare_routing_candidates(loaded)
    assert comparison["count"] == 2
    assert comparison["best_candidate_id"] == "20260824T000001Z"
