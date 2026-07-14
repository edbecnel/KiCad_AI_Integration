"""Tests for shared artifact catalog."""

from pathlib import Path

import pytest

from context.artifacts.catalog import (
    ArtifactEntry,
    Catalog,
    ComponentRef,
    ProjectReference,
)


def test_catalog_bootstrap(tmp_path: Path) -> None:
    catalog = Catalog(tmp_path)
    catalog.bootstrap()
    assert (tmp_path / "catalog.json").is_file()
    assert (tmp_path / "datasheets").is_dir()
    assert (tmp_path / "libs").is_dir()


def test_add_and_get_artifact(tmp_path: Path) -> None:
    catalog = Catalog(tmp_path)
    catalog.bootstrap()
    entry = ArtifactEntry(
        id="ds-TEST-abc123",
        type="datasheet",
        part="F0D3180",
        file="datasheets/F0D3180.pdf",
        sha256="abc",
        source="user_attach",
    )
    catalog.add_artifact(entry)
    assert catalog.get_by_id("ds-TEST-abc123") is not None
    assert len(catalog.get_by_part("F0D3180")) == 1


def test_upsert_reference(tmp_path: Path) -> None:
    catalog = Catalog(tmp_path)
    catalog.bootstrap()
    entry = ArtifactEntry(
        id="ds-TEST-abc123",
        type="datasheet",
        part="F0D3180",
        file="datasheets/F0D3180.pdf",
        sha256="abc",
        source="user_attach",
    )
    catalog.add_artifact(entry)
    proj = ProjectReference(
        project_path="/projects/a/a.kicad_pro",
        project_name="a",
        schematics=["a.kicad_sch"],
    )
    comp = ComponentRef(reference="U3", sheet_path="a.kicad_sch", sheet_name="/")
    catalog.upsert_reference(entry.id, proj, comp)
    updated = catalog.get_by_id(entry.id)
    assert updated is not None
    assert len(updated.referenced_by) == 1
    assert updated.referenced_by[0].components[0].reference == "U3"


def test_can_delete_only_when_unreferenced(tmp_path: Path) -> None:
    catalog = Catalog(tmp_path)
    catalog.bootstrap()
    entry = ArtifactEntry(
        id="ds-TEST-abc123",
        type="datasheet",
        part="F0D3180",
        file="datasheets/F0D3180.pdf",
        sha256="abc",
        source="user_attach",
    )
    catalog.add_artifact(entry)
    assert catalog.can_delete(entry.id) is True
    proj = ProjectReference(
        project_path="/projects/a/a.kicad_pro",
        project_name="a",
    )
    catalog.upsert_reference(
        entry.id,
        proj,
        ComponentRef(reference="U1", sheet_path="a.kicad_sch"),
    )
    assert catalog.can_delete(entry.id) is False
