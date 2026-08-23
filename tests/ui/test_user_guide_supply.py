"""Tests for user guide manifest and path resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from ui.user_guide_supply import (
    load_manifest,
    read_guide_markdown,
    resolve_guide_href,
    user_guides_dir,
)


def test_user_guides_dir_exists() -> None:
    guides = user_guides_dir()
    assert guides.is_dir()
    assert (guides / "README.md").is_file()
    assert (guides / "guide_manifest.json").is_file()


def test_manifest_lists_all_tab_topics() -> None:
    manifest = load_manifest()
    for tab_id in ("chat", "datasheets", "simulation", "aerf", "notebook", "audits", "routing"):
        rel = manifest.path_for_tab(tab_id)
        assert rel.endswith(".md")
        assert (user_guides_dir() / rel).is_file()


def test_manifest_has_step_by_step_section() -> None:
    manifest = load_manifest()
    section_titles = [section.title for section in manifest.sections]
    assert "Step-by-step guides" in section_titles
    step_section = next(s for s in manifest.sections if s.title == "Step-by-step guides")
    assert "step_by_step_hub" in step_section.topic_ids
    assert "workflow_ekm" in step_section.topic_ids
    assert manifest.path_for_topic("step_by_step_hub") == "Step_By_Step_Guides.md"
    assert (user_guides_dir() / "Step_By_Step_Guides.md").is_file()


def test_read_guide_markdown_hub() -> None:
    text = read_guide_markdown("README.md")
    assert "User Guides" in text


def test_resolve_guide_href_relative() -> None:
    resolved = resolve_guide_href("02_Chat.md", "README.md")
    assert resolved == "02_Chat.md"


def test_resolve_guide_href_workflow_relative() -> None:
    resolved = resolve_guide_href("../02_Chat.md", "Workflows/New_Project_to_EKM.md")
    assert resolved == "02_Chat.md"


def test_resolve_guide_href_rejects_escape() -> None:
    assert resolve_guide_href("../../../etc/passwd", "README.md") is None


def test_read_guide_markdown_missing_raises() -> None:
    with pytest.raises(FileNotFoundError):
        read_guide_markdown("missing_guide.md")
