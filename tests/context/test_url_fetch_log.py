"""Tests for persistent URL fetch log and AI discovery handoff."""

from pathlib import Path
from unittest.mock import MagicMock

from context.artifacts.store import ArtifactStore, ProjectContextInfo
from context.datasheet_resolver import DatasheetResolver
from context.schematic_parse import SymbolInstance
from utils.config import AppConfig


def test_url_fetch_log_records_downloaded(tmp_path: Path) -> None:
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    config = AppConfig(artifact_library_path=tmp_path / "lib", datasheet_url_fetch="if_missing")

    def fake_fetch(url, dest, **kwargs):
        dest.write_bytes(b"%PDF-1.4 fetched")
        from utils.url_fetch import FetchResult

        return FetchResult(path=dest, content_type="application/pdf", byte_size=14)

    resolver = DatasheetResolver(config, fetch_fn=fake_fetch, verbose=False)
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[])
    symbol = SymbolInstance(
        reference="U1",
        value="LM7805",
        datasheet="https://example.com/lm7805.pdf",
        sheet_path="p.kicad_sch",
    )
    result = resolver.resolve_all([symbol], project)["U1"]
    assert result.status == "resolved"
    assert result.url_fetch_outcome == "downloaded"

    log = ArtifactStore(config.artifact_library_path).url_fetch_log
    entry = log.get("LM7805", "https://example.com/lm7805.pdf")
    assert entry is not None
    assert entry.status == "downloaded"
    assert entry.artifact_id == result.artifact_id


def test_failed_url_skipped_on_second_run(tmp_path: Path) -> None:
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    config = AppConfig(artifact_library_path=tmp_path / "lib", datasheet_url_fetch="if_missing")
    fetch_fn = MagicMock(side_effect=OSError("timeout"))
    resolver = DatasheetResolver(config, fetch_fn=fetch_fn, verbose=False)
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[])
    symbol = SymbolInstance(
        reference="U1",
        value="LM7805",
        datasheet="https://example.com/lm7805.pdf",
        sheet_path="p.kicad_sch",
    )

    first = resolver.resolve_all([symbol], project)["U1"]
    assert first.status == "fetch_failed"
    assert first.needs_ai_datasheet_discovery is True
    assert first.url_fetch_outcome == "failed"
    assert fetch_fn.call_count == 1

    second = DatasheetResolver(config, fetch_fn=fetch_fn, verbose=False).resolve_all(
        [symbol], project
    )["U1"]
    assert second.status == "fetch_failed"
    assert second.needs_ai_datasheet_discovery is True
    assert "url_fetch_log:failed" in second.sources_tried
    assert fetch_fn.call_count == 1


def test_new_url_retried_after_prior_failure(tmp_path: Path) -> None:
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    config = AppConfig(artifact_library_path=tmp_path / "lib", datasheet_url_fetch="if_missing")
    calls: list[str] = []

    def fake_fetch(url, dest, **kwargs):
        calls.append(url)
        if "bad" in url:
            raise OSError("404")
        dest.write_bytes(b"%PDF-1.4 fetched")
        from utils.url_fetch import FetchResult

        return FetchResult(path=dest, content_type="application/pdf", byte_size=14)

    resolver = DatasheetResolver(config, fetch_fn=fake_fetch, verbose=False)
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[])
    bad = SymbolInstance(
        reference="U1",
        value="LM7805",
        datasheet="https://example.com/bad.pdf",
        sheet_path="p.kicad_sch",
    )
    resolver.resolve_all([bad], project)

    good = SymbolInstance(
        reference="U1",
        value="LM7805",
        datasheet="https://example.com/good.pdf",
        sheet_path="p.kicad_sch",
    )
    result = DatasheetResolver(config, fetch_fn=fake_fetch, verbose=False).resolve_all(
        [good], project
    )["U1"]
    assert result.status == "resolved"
    assert len(calls) == 2


def test_retry_failed_urls_retries_fetch(tmp_path: Path) -> None:
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    config = AppConfig(artifact_library_path=tmp_path / "lib", datasheet_url_fetch="if_missing")
    fetch_fn = MagicMock(side_effect=OSError("timeout"))
    resolver = DatasheetResolver(config, fetch_fn=fetch_fn, verbose=False)
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[])
    symbol = SymbolInstance(
        reference="U1",
        value="LM7805",
        datasheet="https://example.com/lm7805.pdf",
        sheet_path="p.kicad_sch",
    )
    resolver.resolve_all([symbol], project)
    assert fetch_fn.call_count == 1

    DatasheetResolver(config, fetch_fn=fetch_fn, verbose=False).resolve_all(
        [symbol], project, retry_failed_urls=True
    )
    assert fetch_fn.call_count == 2
