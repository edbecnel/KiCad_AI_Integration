"""Tests for per-part Value datasheet reset (selective hard refresh)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from context.artifacts.manifest import Manifest
from context.artifacts.store import ArtifactStore, ProjectContextInfo
from context.datasheet_resolver import DatasheetResolver
from context.schematic_parse import SymbolInstance
from ui.datasheet_supply import manual_pdf_path_for_part, reset_datasheet_for_part
from utils.config import AppConfig
from utils.url_fetch import FetchResult


def _project(tmp_path: Path) -> ProjectContextInfo:
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    sch = tmp_path / "p.kicad_sch"
    sch.touch()
    return ProjectContextInfo(project_pro_path=pro, schematic_paths=[sch])


def _make_pdf(path: Path, content: bytes = b"%PDF-1.4 test") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_reset_clears_manifest_and_url_fetch_log(tmp_path: Path) -> None:
    lib = tmp_path / "lib"
    config = AppConfig(artifact_library_path=lib, datasheet_url_fetch="if_missing")
    project = _project(tmp_path)
    pdf = tmp_path / "FOD3180.pdf"
    _make_pdf(pdf)

    store = ArtifactStore(lib)
    sym = SymbolInstance(
        reference="U1",
        value="FOD3180",
        datasheet="https://example.com/fod3180.pdf",
        sheet_path="p.kicad_sch",
        lib_id="New_Library:FOD3180",
    )
    entry = store.register_datasheet(
        pdf,
        "FOD3180",
        "user_attach",
        project,
        None,
        source_url="https://example.com/fod3180.pdf",
    )
    manifest = Manifest.load(project.project_pro_path)
    manifest.upsert_link(
        entry.id,
        "FOD3180",
        __import__("context.artifacts.manifest", fromlist=["ManifestComponentLink"]).ManifestComponentLink(
            reference="U1",
            sheet_path="p.kicad_sch",
        ),
    )
    manifest.save()
    store.url_fetch_log.record_failed("FOD3180", "https://example.com/fod3180.pdf", error="old")
    store.url_fetch_log.save()

    sch_content = """
(kicad_sch (version 20230121) (generator "test")
  (symbol (lib_id "New_Library:FOD3180") (at 0 0 0) (unit 1)
    (property "Reference" "U1" (at 0 0 0))
    (property "Value" "FOD3180" (at 0 0 0))
    (property "Datasheet" "https://example.com/fod3180-new.pdf" (at 0 0 0))
  )
)
"""
    (tmp_path / "p.kicad_sch").write_text(sch_content, encoding="utf-8")

    def fake_fetch(url, dest, **kwargs):
        dest.write_bytes(b"%PDF-1.4 refetched")
        return FetchResult(path=dest, content_type="application/pdf", byte_size=16)

    # Patch resolver fetch via monkeypatch on DatasheetResolver used in collect
    import context.datasheet_resolver as dr

    original_init = dr.DatasheetResolver.__init__

    def patched_init(self, cfg, store=None, fetch_fn=None, *, verbose=True):
        original_init(self, cfg, store, fetch_fn=fake_fetch, verbose=verbose)

    dr.DatasheetResolver.__init__ = patched_init  # type: ignore[method-assign]
    try:
        ctx = reset_datasheet_for_part(
            project.project_pro_path,
            "FOD3180",
            config=config,
            quarantine_local_pdf=False,
            verbose=False,
        )
    finally:
        dr.DatasheetResolver.__init__ = original_init  # type: ignore[method-assign]

    reloaded_manifest = Manifest.load(project.project_pro_path)
    links = reloaded_manifest.get_links_for_part("FOD3180")
    assert len(links) == 1
    assert links[0].artifact_id == ctx.datasheet_resolutions["U1"].artifact_id
    reloaded_store = ArtifactStore(lib)
    assert reloaded_store.url_fetch_log.get("FOD3180", "https://example.com/fod3180.pdf") is None
    assert reloaded_store.url_fetch_log.get("FOD3180", "https://example.com/fod3180-new.pdf") is not None
    res = ctx.datasheet_resolutions.get("U1")
    assert res is not None
    assert res.status == "resolved"
    assert "catalog_skipped_force_refresh" in res.sources_tried


def test_force_refresh_skips_catalog(tmp_path: Path) -> None:
    lib = tmp_path / "lib"
    config = AppConfig(artifact_library_path=lib, datasheet_url_fetch="if_missing")
    project = _project(tmp_path)
    pdf = tmp_path / "old.pdf"
    _make_pdf(pdf, b"%PDF-1.4 old")

    store = ArtifactStore(lib)
    store.register_datasheet(pdf, "FOD3180", "user_attach", project, None)

    sym = SymbolInstance(
        reference="U1",
        value="FOD3180",
        datasheet="https://example.com/new.pdf",
        sheet_path="p.kicad_sch",
        lib_id="New_Library:FOD3180",
    )

    def fake_fetch(url, dest, **kwargs):
        dest.write_bytes(b"%PDF-1.4 new fetch")
        return FetchResult(path=dest, content_type="application/pdf", byte_size=15)

    resolver = DatasheetResolver(config, store, fetch_fn=fake_fetch, verbose=False)
    result = resolver.resolve_all(
        [sym],
        project,
        retry_failed_urls=True,
        force_refresh_parts={"FOD3180"},
    )["U1"]
    assert result.status == "resolved"
    assert result.artifact_id is not None
    assert "https_fetch" in result.sources_tried
    assert "catalog_skipped_force_refresh" in result.sources_tried


def test_quarantine_local_pdf(tmp_path: Path) -> None:
    lib = tmp_path / "lib"
    config = AppConfig(artifact_library_path=lib)
    pdf_path = manual_pdf_path_for_part(lib, "FOD3180")
    _make_pdf(pdf_path)

    from ui.datasheet_supply import _quarantine_local_pdf_file

    moved = _quarantine_local_pdf_file(pdf_path)
    assert moved is not None
    assert not pdf_path.is_file()
    assert moved.parent.name == ".quarantine"


def test_reset_by_value_all_refs(tmp_path: Path) -> None:
    lib = tmp_path / "lib"
    config = AppConfig(artifact_library_path=lib, datasheet_url_fetch="never")
    project = _project(tmp_path)
    store = ArtifactStore(lib)
    pdf = tmp_path / "shared.pdf"
    _make_pdf(pdf)
    entry = store.register_datasheet(pdf, "FOD3180", "user_attach", project, None)

    sym1 = SymbolInstance(reference="U1", value="FOD3180", sheet_path="p.kicad_sch", lib_id="x:FOD3180")
    sym2 = SymbolInstance(reference="U2", value="FOD3180", sheet_path="p.kicad_sch", lib_id="x:FOD3180")
    manifest = Manifest.load(project.project_pro_path)
    from context.artifacts.manifest import ManifestComponentLink

    for ref in ("U1", "U2"):
        manifest.upsert_link(
            entry.id,
            "FOD3180",
            ManifestComponentLink(reference=ref, sheet_path="p.kicad_sch"),
        )
    manifest.save()

    sch_content = """
(kicad_sch (version 20230121) (generator "test")
  (symbol (lib_id "x:FOD3180") (at 0 0 0) (unit 1)
    (property "Reference" "U1" (at 0 0 0))
    (property "Value" "FOD3180" (at 0 0 0))
    (property "Datasheet" "" (at 0 0 0))
  )
  (symbol (lib_id "x:FOD3180") (at 10 0 0) (unit 1)
    (property "Reference" "U2" (at 0 0 0))
    (property "Value" "FOD3180" (at 0 0 0))
    (property "Datasheet" "" (at 0 0 0))
  )
)
"""
    (tmp_path / "p.kicad_sch").write_text(sch_content, encoding="utf-8")

    ctx = reset_datasheet_for_part(
        project.project_pro_path,
        "FOD3180",
        config=config,
        quarantine_local_pdf=False,
        verbose=False,
    )
    assert ctx.datasheet_resolutions["U1"].status == "missing"
    assert ctx.datasheet_resolutions["U2"].status == "missing"
    assert not Manifest.load(project.project_pro_path).get_links_for_part("FOD3180")


def test_delete_orphan_when_unreferenced(tmp_path: Path) -> None:
    lib = tmp_path / "lib"
    config = AppConfig(artifact_library_path=lib)
    project = _project(tmp_path)
    pdf = tmp_path / "orphan.pdf"
    _make_pdf(pdf)
    store = ArtifactStore(lib)
    entry = store.register_datasheet(pdf, "FOD3180", "user_attach", project, None)
    artifact_id = entry.id
    assert store.catalog.can_delete(artifact_id)

    sch_content = """
(kicad_sch (version 20230121) (generator "test")
  (symbol (lib_id "x:FOD3180") (at 0 0 0) (unit 1)
    (property "Reference" "U1" (at 0 0 0))
    (property "Value" "FOD3180" (at 0 0 0))
    (property "Datasheet" "" (at 0 0 0))
  )
)
"""
    (tmp_path / "p.kicad_sch").write_text(sch_content, encoding="utf-8")

    reset_datasheet_for_part(
        project.project_pro_path,
        "FOD3180",
        config=config,
        delete_orphan_artifact=True,
        quarantine_local_pdf=False,
        verbose=False,
    )
    reloaded_store = ArtifactStore(lib)
    assert reloaded_store.catalog.get_by_id(artifact_id) is None
    assert not (lib / "datasheets" / "FOD3180.pdf").is_file()
