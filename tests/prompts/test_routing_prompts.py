"""Tests for routing policy and post-route review prompts."""

from __future__ import annotations

from context.collector import collect_stretch_context
from prompts.templates.post_route_review import build_post_route_review_prompt
from prompts.templates.routing_policy import build_routing_policy_prompt
from utils.config import AppConfig


def test_build_routing_policy_prompt(blocking_oscillator_pro, isolated_library_config) -> None:
    ctx = collect_stretch_context(blocking_oscillator_pro, config=isolated_library_config)
    system, user = build_routing_policy_prompt(ctx, "Classify critical nets.")
    assert "routing policy" in system.lower()
    assert "user_question" in user


def test_build_post_route_review_prompt(blocking_oscillator_pro, isolated_library_config) -> None:
    ctx = collect_stretch_context(blocking_oscillator_pro, config=isolated_library_config)
    system, user = build_post_route_review_prompt(
        ctx,
        "Review routing quality.",
        routing_result_summary={"success": True},
    )
    assert "autorouted" in system.lower()
    assert "routing_result" in user
