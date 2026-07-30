"""EKM error types."""

from __future__ import annotations


class EKMError(Exception):
    """Base error for EKM operations."""


class EKMValidationError(EKMError):
    """Document failed structural or schema validation."""


class EKMVersionError(EKMError):
    """Unsupported or missing schema_version."""


class EKMIOError(EKMError):
    """Load or save failure."""
