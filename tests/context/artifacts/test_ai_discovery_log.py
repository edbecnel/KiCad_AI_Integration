"""Tests for ai_discovery_log persistence."""

from pathlib import Path

from context.artifacts.ai_discovery_log import AiDiscoveryLog


def test_bootstrap_creates_empty_log(tmp_path: Path) -> None:
    log = AiDiscoveryLog(tmp_path / "lib")
    log.bootstrap()
    assert log.log_path.is_file()
    assert log.entries == []


def test_record_attempt_and_save(tmp_path: Path) -> None:
    log = AiDiscoveryLog(tmp_path / "lib")
    entry = log.record_attempt(
        "FOD3180",
        symbol_datasheet_url="https://example.com/symbol.pdf",
        suggested_urls=["https://onsemi.com/fod3180.pdf"],
        selected_url="https://onsemi.com/fod3180.pdf",
        outcome="fetch_failed",
        error="bot protection",
    )
    assert entry.part == "FOD3180"
    assert entry.outcome == "fetch_failed"
    log.save()

    reloaded = AiDiscoveryLog(tmp_path / "lib")
    latest = reloaded.get_latest("FOD3180")
    assert latest is not None
    assert latest.suggested_urls == ["https://onsemi.com/fod3180.pdf"]
    assert latest.error == "bot protection"


def test_get_latest_returns_most_recent(tmp_path: Path) -> None:
    log = AiDiscoveryLog(tmp_path / "lib")
    log.record_attempt("LM7805", outcome="no_url_found", error="no urls")
    log.record_attempt(
        "LM7805",
        suggested_urls=["https://example.com/lm7805.pdf"],
        outcome="downloaded",
        artifact_id="ds_lm7805",
    )
    log.save()

    latest = AiDiscoveryLog(tmp_path / "lib").get_latest("LM7805")
    assert latest is not None
    assert latest.outcome == "downloaded"
    assert latest.artifact_id == "ds_lm7805"


def test_store_wires_ai_discovery_log(tmp_path: Path) -> None:
    from context.artifacts.store import ArtifactStore

    store = ArtifactStore(tmp_path / "lib")
    store.bootstrap()
    assert store.ai_discovery_log.log_path.is_file()
