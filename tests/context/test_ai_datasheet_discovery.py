"""Tests for AI datasheet discovery (Phase 1)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from context.ai_datasheet_discovery import (
    DiscoveryResult,
    _parse_urls_from_response,
    _validate_suggested_urls,
    format_fetch_attempts_summary,
    run_ai_datasheet_discovery,
)
from context.artifacts.store import ArtifactStore, ProjectContextInfo
from context.datasheet_requirements import format_required_datasheet_notice
from context.datasheet_resolver import DatasheetResolution, DatasheetResolver
from context.schematic_parse import SymbolInstance
from providers.types import ProviderResponse, TokenUsage
from utils.config import AppConfig
from utils.url_fetch import FetchResult, UrlFetchError


class _MockProvider:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.calls: list[str] = []

    def send_message(self, prompt: str, *, system=None, image=None, image_media_type="image/png", config=None):
        self.calls.append(prompt)
        return ProviderResponse(
            text=self.response_text,
            model="mock",
            usage=TokenUsage(input_tokens=10, output_tokens=20),
            stop_reason="end_turn",
            raw={},
        )


def _project(tmp_path: Path) -> ProjectContextInfo:
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    return ProjectContextInfo(project_pro_path=pro, schematic_paths=[])


def _fod3180_symbol(ref: str = "U1") -> SymbolInstance:
    return SymbolInstance(
        reference=ref,
        value="FOD3180",
        datasheet="https://www.mouser.com/datasheet/2/149/FOD3180-1008860.pdf",
        lib_id="New_Library:FOD3180",
        sheet_path="p.kicad_sch",
    )


def _fetch_failed_resolution(symbol: SymbolInstance) -> DatasheetResolution:
    return DatasheetResolution(
        reference=symbol.reference,
        part=symbol.value,
        status="fetch_failed",
        needs_ai_datasheet_discovery=True,
        url_fetch_outcome="failed",
        sources_tried=["fetch_error:bot protection"],
    )


def test_parse_urls_from_response_json() -> None:
    text = '{"urls": ["https://www.onsemi.com/pdf/fod3180.pdf"]}'
    assert _parse_urls_from_response(text) == ["https://www.onsemi.com/pdf/fod3180.pdf"]


def test_parse_urls_from_response_fenced() -> None:
    text = 'Here:\n```json\n{"urls": ["https://example.com/a.pdf"]}\n```'
    assert _parse_urls_from_response(text) == ["https://example.com/a.pdf"]


def test_validate_suggested_urls_rejects_http() -> None:
    def fake_validate(url: str) -> None:
        if url.startswith("http://"):
            raise UrlFetchError("Only https: URLs are allowed")

    with patch("context.ai_datasheet_discovery.validate_url", side_effect=fake_validate):
        valid = _validate_suggested_urls(
            ["http://insecure.com/a.pdf", "https://example.com/a.pdf"]
        )
    assert valid == ["https://example.com/a.pdf"]


def test_eligibility_opt_in_only(tmp_path: Path) -> None:
    config = AppConfig(
        artifact_library_path=tmp_path / "lib",
        datasheet_ai_discovery=False,
        anthropic_api_key="key",
    )
    store = ArtifactStore(config.artifact_library_path)
    sym = _fod3180_symbol()
    resolutions = {sym.reference: _fetch_failed_resolution(sym)}
    provider = _MockProvider('{"urls": ["https://example.com/fod3180.pdf"]}')
    results = run_ai_datasheet_discovery(
        [sym],
        resolutions,
        _project(tmp_path),
        store,
        config,
        provider=provider,
        verbose=False,
    )
    assert results == {}
    assert provider.calls == []


def test_eligibility_skip_resolved(tmp_path: Path) -> None:
    config = AppConfig(
        artifact_library_path=tmp_path / "lib",
        datasheet_ai_discovery=True,
        anthropic_api_key="key",
    )
    store = ArtifactStore(config.artifact_library_path)
    sym = _fod3180_symbol()
    resolutions = {
        sym.reference: DatasheetResolution(
            reference=sym.reference,
            part=sym.value,
            status="resolved",
            artifact_id="ds_fod3180",
        )
    }
    provider = _MockProvider('{"urls": ["https://example.com/fod3180.pdf"]}')
    results = run_ai_datasheet_discovery(
        [sym],
        resolutions,
        _project(tmp_path),
        store,
        config,
        provider=provider,
        verbose=False,
    )
    assert results == {}
    assert provider.calls == []


def test_mock_claude_success_registers_artifact(tmp_path: Path) -> None:
    config = AppConfig(
        artifact_library_path=tmp_path / "lib",
        datasheet_ai_discovery=True,
        datasheet_ai_discovery_auto_fetch=True,
        anthropic_api_key="key",
    )
    store = ArtifactStore(config.artifact_library_path)
    sym = _fod3180_symbol()
    resolutions = {sym.reference: _fetch_failed_resolution(sym)}
    ai_url = "https://www.onsemi.com/pdf/fod3180-d.pdf"
    provider = _MockProvider(f'{{"urls": ["{ai_url}"]}}')

    def fake_fetch(url, dest, **kwargs):
        dest.write_bytes(b"%PDF-1.4 ai fetched")
        return FetchResult(path=dest, content_type="application/pdf", byte_size=18)

    with patch("context.ai_datasheet_discovery.validate_url"):
        results = run_ai_datasheet_discovery(
        [sym],
        resolutions,
        _project(tmp_path),
        store,
        config,
        provider=provider,
        fetch_fn=fake_fetch,
            verbose=False,
        )
    assert results["FOD3180"].outcome == "downloaded"
    assert results["FOD3180"].artifact_id is not None
    entry = store.catalog.get_by_part("FOD3180", "datasheet")[0]
    assert entry.source == "ai_discovery"
    log_entry = store.ai_discovery_log.get_latest("FOD3180")
    assert log_entry is not None
    assert log_entry.outcome == "downloaded"
    assert ai_url in log_entry.suggested_urls


def test_failure_records_both_logs(tmp_path: Path) -> None:
    config = AppConfig(
        artifact_library_path=tmp_path / "lib",
        datasheet_ai_discovery=True,
        datasheet_ai_discovery_auto_fetch=True,
        anthropic_api_key="key",
    )
    store = ArtifactStore(config.artifact_library_path)
    sym = _fod3180_symbol()
    resolutions = {sym.reference: _fetch_failed_resolution(sym)}
    ai_url = "https://www.onsemi.com/pdf/fod3180-d.pdf"
    provider = _MockProvider(f'{{"urls": ["{ai_url}"]}}')
    fetch_fn = MagicMock(side_effect=UrlFetchError("bot protection"))

    with patch("context.ai_datasheet_discovery.validate_url"), patch(
        "context.ai_datasheet_discovery.heuristic_datasheet_urls", return_value=[]
    ):
        results = run_ai_datasheet_discovery(
            [sym],
            resolutions,
            _project(tmp_path),
            store,
            config,
            provider=provider,
            fetch_fn=fetch_fn,
            verbose=False,
        )
    assert results["FOD3180"].outcome == "fetch_failed"
    assert "bot protection" in (results["FOD3180"].error or "")
    assert len(results["FOD3180"].fetch_attempts) == 1
    assert results["FOD3180"].fetch_attempts[0][0] == ai_url
    url_log = store.url_fetch_log.get("FOD3180", ai_url)
    assert url_log is not None
    assert url_log.status == "failed"
    discovery_log = store.ai_discovery_log.get_latest("FOD3180")
    assert discovery_log is not None
    assert discovery_log.outcome == "fetch_failed"


def test_dedupe_by_value(tmp_path: Path) -> None:
    config = AppConfig(
        artifact_library_path=tmp_path / "lib",
        datasheet_ai_discovery=True,
        datasheet_ai_discovery_auto_fetch=True,
        anthropic_api_key="key",
    )
    store = ArtifactStore(config.artifact_library_path)
    sym1 = _fod3180_symbol("U1")
    sym2 = _fod3180_symbol("U2")
    sym2.reference = "U2"
    resolutions = {
        sym1.reference: _fetch_failed_resolution(sym1),
        sym2.reference: _fetch_failed_resolution(sym2),
    }
    provider = _MockProvider('{"urls": ["https://example.com/fod3180.pdf"]}')

    def fake_fetch(url, dest, **kwargs):
        dest.write_bytes(b"%PDF-1.4")
        return FetchResult(path=dest, content_type="application/pdf", byte_size=8)

    with patch("context.ai_datasheet_discovery.validate_url"):
        results = run_ai_datasheet_discovery(
            [sym1, sym2],
            resolutions,
            _project(tmp_path),
            store,
            config,
            provider=provider,
            fetch_fn=fake_fetch,
            verbose=False,
        )
    assert len(results) == 1
    assert len(provider.calls) == 1


def test_failure_message_format(tmp_path: Path) -> None:
    sym = _fod3180_symbol()
    res = _fetch_failed_resolution(sym)
    discovery = DiscoveryResult(
        part="FOD3180",
        outcome="fetch_failed",
        suggested_urls=["https://www.onsemi.com/pdf/fod3180-d.pdf"],
        selected_url="https://www.onsemi.com/pdf/fod3180-d.pdf",
        error="Site blocked automated download (bot protection)",
    )
    notice = format_required_datasheet_notice(
        [sym],
        {sym.reference: res},
        library_path=tmp_path / "lib",
        ai_discovery_results={"FOD3180": discovery},
    )
    assert notice is not None
    assert "FOD3180" in notice
    assert "AI discovery failed" in notice
    assert "bot protection" in notice
    assert sym.datasheet in notice
    assert "onsemi.com" in notice
    assert "datasheets/FOD3180.pdf" in notice


def test_fod3180_scenario_handoff_message(tmp_path: Path) -> None:
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    config = AppConfig(
        artifact_library_path=tmp_path / "lib",
        datasheet_url_fetch="if_missing",
        datasheet_ai_discovery=True,
        datasheet_ai_discovery_auto_fetch=True,
        anthropic_api_key="key",
    )

    def fail_fetch(url, dest, **kwargs):
        raise UrlFetchError("Site blocked automated download (bot protection)")

    provider = _MockProvider(
        '{"urls": ["https://www.onsemi.com/download/data-sheet/pdf/fod3180-d.pdf"]}'
    )

    sym = _fod3180_symbol()
    # Patch resolver fetch in collector by pre-running isn't easy; test discovery module directly
    store = ArtifactStore(config.artifact_library_path)
    store.url_fetch_log.record_failed(
        "FOD3180",
        sym.datasheet,
        error="Site blocked automated download (bot protection)",
    )
    store.url_fetch_log.save()
    resolutions = {sym.reference: _fetch_failed_resolution(sym)}

    with patch("context.ai_datasheet_discovery.validate_url"):
        results = run_ai_datasheet_discovery(
            [sym],
            resolutions,
            _project(tmp_path),
            store,
            config,
            provider=provider,
            fetch_fn=fail_fetch,
            verbose=False,
        )
    assert results["FOD3180"].outcome == "fetch_failed"
    notice = format_required_datasheet_notice(
        [sym],
        resolutions,
        library_path=config.artifact_library_path,
        ai_discovery_results=results,
    )
    assert notice is not None
    assert "Suggested URL" in notice


def test_only_parts_skips_other_values(tmp_path: Path) -> None:
    config = AppConfig(
        artifact_library_path=tmp_path / "lib",
        datasheet_ai_discovery=True,
        datasheet_ai_discovery_auto_fetch=True,
        anthropic_api_key="key",
    )
    store = ArtifactStore(config.artifact_library_path)
    sym_fod = _fod3180_symbol("U1")
    sym_other = SymbolInstance(
        reference="Q1",
        value="BD243C",
        datasheet="https://example.invalid/bd243c.pdf",
        lib_id="Device:Q_NPN",
        sheet_path="p.kicad_sch",
    )
    resolutions = {
        sym_fod.reference: _fetch_failed_resolution(sym_fod),
        sym_other.reference: _fetch_failed_resolution(sym_other),
    }
    provider = _MockProvider('{"urls": ["https://example.com/fod3180.pdf"]}')

    def ok_fetch(url: str, dest: Path, **kwargs: object) -> FetchResult:
        dest.write_bytes(b"%PDF-1.4 test")
        return FetchResult(path=dest, content_type="application/pdf", byte_size=12)

    with patch("context.ai_datasheet_discovery.validate_url"):
        results = run_ai_datasheet_discovery(
            [sym_fod, sym_other],
            resolutions,
            _project(tmp_path),
            store,
            config,
            provider=provider,
            fetch_fn=ok_fetch,
            only_parts={"FOD3180"},
            verbose=False,
        )
    assert "FOD3180" in results
    assert "BD243C" not in results
    assert len(provider.calls) == 1


def test_approve_auto_tries_remaining_urls_after_fetch_fail(tmp_path: Path) -> None:
    config = AppConfig(
        artifact_library_path=tmp_path / "lib",
        datasheet_ai_discovery=True,
        datasheet_ai_discovery_auto_fetch=False,
        anthropic_api_key="key",
    )
    store = ArtifactStore(config.artifact_library_path)
    sym = _fod3180_symbol()
    resolutions = {sym.reference: _fetch_failed_resolution(sym)}
    provider = _MockProvider(
        '{"urls": ["https://example.com/bad.pdf", "https://example.com/good.pdf"]}'
    )
    approvals: list[list[str]] = []

    def approve(_part: str, urls: list[str]) -> str | None:
        approvals.append(list(urls))
        return urls[0]

    def fetch(url: str, dest: Path, **kwargs: object) -> FetchResult:
        if url.endswith("bad.pdf"):
            raise UrlFetchError("Site blocked automated download (bot protection)")
        dest.write_bytes(b"%PDF-1.4 good")
        return FetchResult(path=dest, content_type="application/pdf", byte_size=12)

    with patch("context.ai_datasheet_discovery.validate_url"), patch(
        "context.ai_datasheet_discovery.heuristic_datasheet_urls", return_value=[]
    ):
        results = run_ai_datasheet_discovery(
            [sym],
            resolutions,
            _project(tmp_path),
            store,
            config,
            provider=provider,
            fetch_fn=fetch,
            approve_url=approve,
            verbose=False,
        )
    assert results["FOD3180"].outcome == "downloaded"
    assert len(approvals) == 1
    assert len(approvals[0]) == 2
    assert len(results["FOD3180"].fetch_attempts) == 2
    assert results["FOD3180"].fetch_attempts[0][1] is not None
    assert results["FOD3180"].fetch_attempts[1][1] is None


def test_on_fetch_attempt_callback(tmp_path: Path) -> None:
    config = AppConfig(
        artifact_library_path=tmp_path / "lib",
        datasheet_ai_discovery=True,
        datasheet_ai_discovery_auto_fetch=True,
        anthropic_api_key="key",
    )
    store = ArtifactStore(config.artifact_library_path)
    sym = _fod3180_symbol()
    resolutions = {sym.reference: _fetch_failed_resolution(sym)}
    provider = _MockProvider(
        '{"urls": ["https://example.com/bad.pdf", "https://example.com/good.pdf"]}'
    )
    events: list[tuple[str, str, str | None]] = []

    def fetch(url: str, dest: Path, **kwargs: object) -> FetchResult:
        if url.endswith("bad.pdf"):
            raise UrlFetchError("blocked")
        dest.write_bytes(b"%PDF-1.4")
        return FetchResult(path=dest, content_type="application/pdf", byte_size=8)

    with patch("context.ai_datasheet_discovery.validate_url"), patch(
        "context.ai_datasheet_discovery.heuristic_datasheet_urls", return_value=[]
    ):
        run_ai_datasheet_discovery(
            [sym],
            resolutions,
            _project(tmp_path),
            store,
            config,
            provider=provider,
            fetch_fn=fetch,
            on_fetch_attempt=lambda part, url, err: events.append((part, url, err)),
            verbose=False,
        )
    assert len(events) == 2
    assert events[0][2] == "blocked"
    assert events[1][2] is None


def test_format_fetch_attempts_summary_lists_untried() -> None:
    summary = format_fetch_attempts_summary(
        [("https://example.com/a.pdf", "bot protection")],
        suggested_urls=[
            "https://example.com/a.pdf",
            "https://example.com/b.pdf",
        ],
    )
    assert "FAIL" in summary
    assert "a.pdf" in summary
    assert "Not attempted" in summary
    assert "b.pdf" in summary
    assert "Attach PDF" in summary


def test_heuristics_preferred_over_ai_portal_url(tmp_path: Path) -> None:
    config = AppConfig(
        artifact_library_path=tmp_path / "lib",
        datasheet_ai_discovery=True,
        datasheet_ai_discovery_auto_fetch=False,
        anthropic_api_key="key",
    )
    store = ArtifactStore(config.artifact_library_path)
    sym = SymbolInstance(
        reference="Q1",
        value="BD243C",
        datasheet="https://example.invalid/bd243c.pdf",
        lib_id="Device:Q_NPN",
        sheet_path="p.kicad_sch",
    )
    resolutions = {sym.reference: _fetch_failed_resolution(sym)}
    portal = "https://www.onsemi.com/design/technical-documentation?notFound=bd243-d.pdf"
    provider = _MockProvider(f'{{"urls": ["{portal}"]}}')
    approved: list[str] = []

    def approve(_part: str, urls: list[str]) -> str | None:
        approved.append(urls[0])
        return urls[0]

    def fetch(url: str, dest: Path, **kwargs: object) -> FetchResult:
        if "bd243b-d.pdf" in url:
            dest.write_bytes(b"%PDF-1.4")
            return FetchResult(path=dest, content_type="application/pdf", byte_size=8)
        raise UrlFetchError("404")

    with patch("context.ai_datasheet_discovery.validate_url"):
        results = run_ai_datasheet_discovery(
            [sym],
            resolutions,
            _project(tmp_path),
            store,
            config,
            provider=provider,
            fetch_fn=fetch,
            approve_url=approve,
            verbose=False,
        )
    assert approved[0].endswith("bd243c-d.pdf")
    assert portal not in results["BD243C"].suggested_urls
    assert any("bd243" in u for u in results["BD243C"].suggested_urls)


def test_user_approval_rejected(tmp_path: Path) -> None:
    config = AppConfig(
        artifact_library_path=tmp_path / "lib",
        datasheet_ai_discovery=True,
        datasheet_ai_discovery_auto_fetch=False,
        anthropic_api_key="key",
    )
    store = ArtifactStore(config.artifact_library_path)
    sym = _fod3180_symbol()
    resolutions = {sym.reference: _fetch_failed_resolution(sym)}
    provider = _MockProvider('{"urls": ["https://example.com/fod3180.pdf"]}')

    with patch("context.ai_datasheet_discovery.validate_url"):
        results = run_ai_datasheet_discovery(
            [sym],
            resolutions,
            _project(tmp_path),
            store,
            config,
            provider=provider,
            approve_url=lambda _part, _urls: None,
            verbose=False,
        )
    assert results["FOD3180"].outcome == "user_rejected"
    assert store.ai_discovery_log.get_latest("FOD3180").outcome == "user_rejected"
