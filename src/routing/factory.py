"""Routing engine factory."""

from __future__ import annotations

from routing.freerouting import FreeroutingRoutingEngine
from utils.config import AppConfig


def get_routing_engine(config: AppConfig | None = None) -> FreeroutingRoutingEngine:
    """Return the configured routing engine (Freerouting reference implementation)."""
    cfg = config
    jar = cfg.freerouting_jar if cfg else None
    cli = cfg.freerouting_cli if cfg else None
    return FreeroutingRoutingEngine(jar=jar, cli=cli)
