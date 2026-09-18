"""HTTPS TLS context helpers for stdlib urllib (KiCad embedded Python on macOS)."""

from __future__ import annotations

import os
import ssl
import urllib.request
from typing import Any


def default_ssl_context() -> ssl.SSLContext:
    """
    Build an SSL context for outbound HTTPS.

    KiCad's embedded Python on macOS often lacks a CA bundle; prefer certifi when
    installed, or SSL_CERT_FILE / REQUESTS_CA_BUNDLE when set.
    """
    for env_name in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"):
        path = (os.environ.get(env_name) or "").strip()
        if path and os.path.isfile(path):
            return ssl.create_default_context(cafile=path)

    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def urlopen_https(
    request: urllib.request.Request,
    timeout: float | None = None,
    *,
    context: ssl.SSLContext | None = None,
) -> Any:
    """urllib.request.urlopen with a CA bundle suitable for KiCad/macOS."""
    return urllib.request.urlopen(
        request,
        timeout=timeout,
        context=context or default_ssl_context(),
    )
