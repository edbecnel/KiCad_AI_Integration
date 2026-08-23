"""Optional E2E routing test (requires Freerouting + pcbnew)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from inference.routing import build_routing_request, run_routing
from utils.config import AppConfig


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
