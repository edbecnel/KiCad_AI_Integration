"""Tests for URL dedupe and fetch policy in datasheet resolver."""

from pathlib import Path
from unittest.mock import MagicMock

from context.artifacts.store import ArtifactStore, ProjectContextInfo
from context.datasheet_resolver import DatasheetResolver, normalize_datasheet_url
from context.schematic_parse import SymbolInstance
from utils.config import AppConfig


def test_normalize_datasheet_url() -> None:
    assert normalize_datasheet_url("https://Example.COM/path/") == normalize_datasheet_url(
        "https://example.com/path"
    )


def test_https_fetch_deduped_by_url(tmp_path: Path) -> None:
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    config = AppConfig(artifact_library_path=tmp_path / "lib", datasheet_url_fetch="if_missing")
    fetch_calls: list[str] = []

    def fake_fetch(url, dest, **kwargs):
        fetch_calls.append(url)
        dest.write_bytes(b"%PDF-1.4 fetched")
        from utils.url_fetch import FetchResult

        return FetchResult(path=dest, content_type="application/pdf", byte_size=14)

    resolver = DatasheetResolver(config, fetch_fn=fake_fetch, verbose=False)
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[])
    symbols = [
        SymbolInstance(
            reference="U1",
            value="PART-A",
            datasheet="https://example.com/a.pdf",
            sheet_path="p.kicad_sch",
        ),
        SymbolInstance(
            reference="U2",
            value="PART-B",
            datasheet="https://example.com/a.pdf",
            sheet_path="p.kicad_sch",
        ),
    ]
    results = resolver.resolve_all(symbols, project)
    assert results["U1"].status == "resolved"
    assert results["U2"].status == "resolved"
    assert len(fetch_calls) == 1


def test_if_missing_is_default(tmp_path: Path) -> None:
    config = AppConfig(artifact_library_path=tmp_path / "lib")
    assert config.datasheet_url_fetch == "if_missing"


def test_if_missing_skips_fetch_when_catalog_has_pdf(tmp_path: Path) -> None:
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    lib = tmp_path / "lib"
    store = ArtifactStore(lib)
    pdf = tmp_path / "cached.pdf"
    pdf.write_bytes(b"%PDF-1.4 cached")
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[])
    entry = store.register_datasheet(
        pdf, "LM7805", "user_attach", project, None, source_url="https://example.com/lm7805.pdf"
    )

    fetch_fn = MagicMock()
    config = AppConfig(artifact_library_path=lib, datasheet_url_fetch="if_missing")
    resolver = DatasheetResolver(config, store=store, fetch_fn=fetch_fn, verbose=False)
    symbol = SymbolInstance(
        reference="U1",
        value="LM7805",
        datasheet="https://example.com/lm7805.pdf",
        sheet_path="p.kicad_sch",
    )
    result = resolver.resolve_all([symbol], project)["U1"]
    assert result.status == "resolved"
    assert result.artifact_id == entry.id
    fetch_fn.assert_not_called()


def test_always_refetches_even_when_cached(tmp_path: Path) -> None:
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    lib = tmp_path / "lib"
    store = ArtifactStore(lib)
    pdf = tmp_path / "cached.pdf"
    pdf.write_bytes(b"%PDF-1.4 cached")
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[])
    store.register_datasheet(
        pdf, "LM7805", "user_attach", project, None, source_url="https://example.com/lm7805.pdf"
    )

    fetch_calls: list[str] = []

    def fake_fetch(url, dest, **kwargs):
        fetch_calls.append(url)
        dest.write_bytes(b"%PDF-1.4 refreshed")
        from utils.url_fetch import FetchResult

        return FetchResult(path=dest, content_type="application/pdf", byte_size=16)

    config = AppConfig(artifact_library_path=lib, datasheet_url_fetch="always")
    resolver = DatasheetResolver(config, store=store, fetch_fn=fake_fetch, verbose=False)
    symbol = SymbolInstance(
        reference="U1",
        value="LM7805",
        datasheet="https://example.com/lm7805.pdf",
        sheet_path="p.kicad_sch",
    )
    result = resolver.resolve_all([symbol], project)["U1"]
    assert result.status == "resolved"
    assert len(fetch_calls) == 1


def test_never_skips_fetch(tmp_path: Path) -> None:
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    config = AppConfig(artifact_library_path=tmp_path / "lib", datasheet_url_fetch="never")
    fetch_fn = MagicMock()
    resolver = DatasheetResolver(config, fetch_fn=fetch_fn, verbose=False)
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[])
    symbol = SymbolInstance(
        reference="U1",
        value="LM7805",
        datasheet="https://example.com/lm7805.pdf",
        sheet_path="p.kicad_sch",
    )
    result = resolver.resolve_all([symbol], project)["U1"]
    assert result.status == "missing"
    assert "https_fetch_disabled" in result.sources_tried
    fetch_fn.assert_not_called()


def test_library_datasheets_folder_resolves_by_part_value(tmp_path: Path) -> None:
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    lib = tmp_path / "lib"
    ds_dir = lib / "datasheets"
    ds_dir.mkdir(parents=True)
    (ds_dir / "FOD3180.pdf").write_bytes(b"%PDF-1.4 local")

    fetch_fn = MagicMock()
    config = AppConfig(artifact_library_path=lib, datasheet_url_fetch="if_missing")
    resolver = DatasheetResolver(config, fetch_fn=fetch_fn, verbose=False)
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[])
    symbol = SymbolInstance(
        reference="U2",
        value="FOD3180",
        datasheet="https://example.com/blocked.pdf",
        sheet_path="p.kicad_sch",
    )
    result = resolver.resolve_all([symbol], project)["U2"]
    assert result.status == "resolved"
    assert "library_datasheet_file" in result.sources_tried
    fetch_fn.assert_not_called()


def test_failed_url_skipped_when_local_pdf_present(tmp_path: Path) -> None:
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    lib = tmp_path / "lib"
    config = AppConfig(artifact_library_path=lib, datasheet_url_fetch="if_missing")
    fetch_fn = MagicMock(side_effect=OSError("timeout"))
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[])
    symbol = SymbolInstance(
        reference="U1",
        value="LM7805",
        datasheet="https://example.com/lm7805.pdf",
        sheet_path="p.kicad_sch",
    )

    first = DatasheetResolver(config, fetch_fn=fetch_fn, verbose=False).resolve_all(
        [symbol], project
    )["U1"]
    assert first.status == "fetch_failed"
    assert fetch_fn.call_count == 1

    ds_dir = lib / "datasheets"
    ds_dir.mkdir(parents=True, exist_ok=True)
    (ds_dir / "LM7805.pdf").write_bytes(b"%PDF-1.4 local")

    result = DatasheetResolver(config, fetch_fn=fetch_fn, verbose=False).resolve_all(
        [symbol], project
    )["U1"]
    assert result.status == "resolved"
    assert fetch_fn.call_count == 1
    assert "library_datasheet_file" in result.sources_tried


def test_retry_failed_dedupes_url_within_run(tmp_path: Path) -> None:
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    config = AppConfig(artifact_library_path=tmp_path / "lib", datasheet_url_fetch="if_missing")
    fetch_fn = MagicMock(side_effect=OSError("timeout"))
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[])
    url = "https://example.com/shared.pdf"
    symbols = [
        SymbolInstance(
            reference="U1",
            value="PART-A",
            datasheet=url,
            sheet_path="p.kicad_sch",
        ),
        SymbolInstance(
            reference="U2",
            value="PART-B",
            datasheet=url,
            sheet_path="p.kicad_sch",
        ),
    ]

    DatasheetResolver(config, fetch_fn=fetch_fn, verbose=False).resolve_all(symbols, project)
    assert fetch_fn.call_count == 1

    DatasheetResolver(config, fetch_fn=fetch_fn, verbose=False).resolve_all(
        symbols, project, retry_failed_urls=True
    )
    assert fetch_fn.call_count == 2
