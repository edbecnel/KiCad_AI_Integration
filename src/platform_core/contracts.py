"""Host-neutral contracts for the platform layer."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DesignSnapshot(Protocol):
    """Ephemeral extracted design facts produced by a host integration layer.

    KiCad reference implementation: ``context.model.ProjectContext``.
    """

    project_path: str
    project_name: str

    def to_dict(self, *, include_image_bytes: bool = False) -> dict[str, Any]: ...

    def to_json(self, *, include_image_bytes: bool = False, indent: int = 2) -> str: ...
