"""Tests for HTTPS SSL context helpers."""

from __future__ import annotations

import ssl
from unittest.mock import patch

import pytest

from utils.ssl_context import default_ssl_context, urlopen_https


def test_default_ssl_context_returns_ssl_context() -> None:
    ctx = default_ssl_context()
    assert isinstance(ctx, ssl.SSLContext)


def test_default_ssl_context_uses_ssl_cert_file_when_set(tmp_path) -> None:
    pem = tmp_path / "bundle.pem"
    pem.write_text("placeholder", encoding="utf-8")
    sentinel = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    with patch.dict("os.environ", {"SSL_CERT_FILE": str(pem)}, clear=False):
        with patch("utils.ssl_context.ssl.create_default_context", return_value=sentinel) as mock_create:
            ctx = default_ssl_context()
    mock_create.assert_called_once_with(cafile=str(pem))
    assert ctx is sentinel


def test_urlopen_https_passes_context(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout=None, context=None):
        captured["context"] = context
        raise OSError("stop")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    import urllib.request

    req = urllib.request.Request("https://example.com")
    with pytest.raises(OSError, match="stop"):
        urlopen_https(req, timeout=5.0)
    assert isinstance(captured.get("context"), ssl.SSLContext)
