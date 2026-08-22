"""RoutingEngine protocol."""

from __future__ import annotations

from typing import Protocol

from routing.types import RoutingEngineCapabilities, RoutingRequest, RoutingResult


class RoutingEngine(Protocol):
    """Replaceable PCB routing engine contract (ADP-013)."""

    def capabilities(self) -> RoutingEngineCapabilities: ...

    def route(self, request: RoutingRequest) -> RoutingResult: ...
