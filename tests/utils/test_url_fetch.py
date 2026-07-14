"""Tests for SSRF-safe URL fetch."""

from pathlib import Path
from unittest.mock import patch

import pytest

from utils.url_fetch import UrlFetchError, fetch_url_to_file, validate_url


def test_reject_http_scheme() -> None:
    with pytest.raises(UrlFetchError, match="https"):
        validate_url("http://example.com/doc.pdf")


def test_reject_localhost() -> None:
    with pytest.raises(UrlFetchError):
        validate_url("https://localhost/secret.pdf")


def test_fetch_with_mock_opener(tmp_path: Path) -> None:
    dest = tmp_path / "out.pdf"
    body = b"%PDF-1.4 mock content"

    class FakeResponse:
        headers = {"Content-Type": "application/pdf"}

        def read(self, size: int = -1) -> bytes:
            if not hasattr(self, "_sent"):
                self._sent = True
                return body
            return b""

        def __enter__(self):
            return self

        def __exit__(self, *args: object) -> None:
            pass

    def fake_opener(request, timeout=30):
        return FakeResponse()

    with patch("utils.url_fetch._resolve_host_ips", return_value=["93.184.216.34"]):
        result = fetch_url_to_file(
            "https://example.com/lm7805.pdf",
            dest,
            opener=fake_opener,
        )
    assert result.byte_size == len(body)
    assert dest.read_bytes() == body


def test_fetch_uses_connect_and_read_timeouts(tmp_path: Path) -> None:
    dest = tmp_path / "out.pdf"
    body = b"%PDF-1.4 mock content"
    seen: list[tuple[float, float]] = []

    def fake_https_fetch(url, **kwargs):
        seen.append((kwargs["connect_timeout"], kwargs["read_timeout"]))
        return body, "application/pdf"

    with patch("utils.url_fetch._resolve_host_ips", return_value=["93.184.216.34"]):
        with patch("utils.url_fetch._urllib_fetch_bytes", side_effect=fake_https_fetch):
            fetch_url_to_file(
                "https://example.com/lm7805.pdf",
                dest,
                timeout_sec=10,
                read_timeout_sec=60,
            )
    assert seen == [(10.0, 60.0)]


def test_bot_wall_html_raises_clear_error() -> None:
    html = b"<!DOCTYPE html><title>Access to this page has been denied.</title>"
    with pytest.raises(UrlFetchError, match="bot protection"):
        from utils.url_fetch import _check_bot_wall

        _check_bot_wall(html, "text/html", status=200)
