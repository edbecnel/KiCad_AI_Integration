"""Headless helpers for the Engineering Notebook UI."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from ekm.view_model import EKMViewModel, FieldView, SearchHit, SectionView
from utils.config import load_config

__all__ = [
    "EKMViewModel",
    "FieldView",
    "SearchHit",
    "SectionView",
    "create_view_model",
]


def _default_attachment_resolver(artifact_id: str) -> str:
    try:
        from context.artifacts.catalog import Catalog

        cfg = load_config()
        catalog = Catalog(cfg.artifact_library_path)
        entry = catalog.get_by_id(artifact_id)
        if entry is None:
            return f"{artifact_id} (not found)"
        return f"{entry.id} — {entry.part} ({entry.file})"
    except OSError:
        return f"{artifact_id} (catalog unavailable)"


def create_view_model(
    project_path: Path | str,
    *,
    attachment_resolver: Callable[[str], str] | None = None,
) -> EKMViewModel:
    resolver = attachment_resolver or _default_attachment_resolver
    return EKMViewModel.from_project(project_path, attachment_resolver=resolver)
