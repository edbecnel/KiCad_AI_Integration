"""Routing engine errors."""

from __future__ import annotations


class RoutingEngineError(Exception):
    """Base error for routing engine operations."""


class RoutingToolNotFoundError(RoutingEngineError, FileNotFoundError):
    """Raised when an external routing tool cannot be located."""


class RoutingExportError(RoutingEngineError):
    """Raised when host DSN/format export fails."""


class RoutingImportError(RoutingEngineError):
    """Raised when host SES/format import fails."""


class RoutingSubprocessError(RoutingEngineError):
    """Raised when the routing subprocess fails."""
