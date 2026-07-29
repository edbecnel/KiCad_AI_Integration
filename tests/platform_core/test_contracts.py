"""Tests for platform contracts."""

from __future__ import annotations

from context.model import ProjectContext
from platform_core.contracts import DesignSnapshot


def test_project_context_satisfies_design_snapshot() -> None:
    ctx = ProjectContext(project_path="/tmp/proj", project_name="proj")
    assert isinstance(ctx, DesignSnapshot)
    data = ctx.to_dict()
    assert data["project_path"] == "/tmp/proj"
    assert data["project_name"] == "proj"
