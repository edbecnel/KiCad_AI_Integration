"""Tests for artifact store deduplication and linking."""

from pathlib import Path

import pytest

from context.artifacts.catalog import ComponentRef
from context.artifacts.store import ArtifactDeletionError, ArtifactStore, ProjectContextInfo


def _make_pdf(path: Path, content: bytes = b"%PDF-1.4 test") -> Path:
    path.write_bytes(content)
    return path


def _project_ctx(tmp_path: Path, name: str = "testproj") -> ProjectContextInfo:
    pro = tmp_path / f"{name}.kicad_pro"
    pro.touch()
    sch = tmp_path / f"{name}.kicad_sch"
    sch.touch()
    return ProjectContextInfo(project_pro_path=pro, schematic_paths=[sch])


def test_register_datasheet_creates_catalog_entry(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    store = ArtifactStore(lib)
    pdf = _make_pdf(tmp_path / "F0D3180.pdf")
    project = _project_ctx(tmp_path)
    comp = ComponentRef(reference="U3", sheet_path="testproj.kicad_sch")
    entry = store.register_datasheet(pdf, "F0D3180", "user_attach", project, comp)
    assert entry.part == "F0D3180"
    assert (lib / "datasheets" / "F0D3180.pdf").is_file()
    assert (tmp_path / "kicad_ai" / "project_manifest.json").is_file()


def test_duplicate_pdf_links_only(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    store = ArtifactStore(lib)
    pdf = _make_pdf(tmp_path / "F0D3180.pdf")
    project_a = _project_ctx(tmp_path, "proj_a")
    project_b_dir = tmp_path / "proj_b"
    project_b_dir.mkdir()
    pro_b = project_b_dir / "proj_b.kicad_pro"
    pro_b.touch()
    sch_b = project_b_dir / "proj_b.kicad_sch"
    sch_b.touch()
    project_b = ProjectContextInfo(project_pro_path=pro_b, schematic_paths=[sch_b])

    entry1 = store.register_datasheet(
        pdf, "F0D3180", "user_attach", project_a,
        ComponentRef(reference="U3", sheet_path="proj_a.kicad_sch"),
    )
    entry2 = store.register_datasheet(
        pdf, "F0D3180", "user_attach", project_b,
        ComponentRef(reference="U1", sheet_path="proj_b.kicad_sch"),
    )
    assert entry1.id == entry2.id
    assert len(list((lib / "datasheets").glob("*.pdf"))) == 1
    updated = store.catalog.get_by_id(entry1.id)
    assert updated is not None
    assert len(updated.referenced_by) == 2


def test_different_hash_same_part_two_entries(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    store = ArtifactStore(lib)
    pdf1 = _make_pdf(tmp_path / "v1.pdf", b"%PDF v1")
    pdf2 = _make_pdf(tmp_path / "v2.pdf", b"%PDF v2")
    project = _project_ctx(tmp_path)
    store.register_datasheet(pdf1, "F0D3180", "user_attach", project)
    store.register_datasheet(pdf2, "F0D3180", "user_attach", project)
    entries = store.get_by_part("F0D3180", "datasheet")
    assert len(entries) == 2


def test_delete_blocked_when_referenced(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    store = ArtifactStore(lib)
    pdf = _make_pdf(tmp_path / "part.pdf")
    project = _project_ctx(tmp_path)
    entry = store.register_datasheet(
        pdf, "PART", "user_attach", project,
        ComponentRef(reference="U1", sheet_path="testproj.kicad_sch"),
    )
    with pytest.raises(ArtifactDeletionError):
        store.delete_artifact(entry.id)
