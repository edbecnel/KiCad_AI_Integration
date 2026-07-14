"""SSRF-safe HTTPS fetch for datasheet URLs."""

from __future__ import annotations

import http.client
import http.cookiejar
import ipaddress
import re
import socket
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlparse

DEFAULT_MAX_BYTES = 25 * 1024 * 1024
DEFAULT_CONNECT_TIMEOUT_SEC = 10
DEFAULT_READ_TIMEOUT_SEC = 60
DEFAULT_DNS_TIMEOUT_SEC = 5
MAX_REDIRECTS = 10

DEFAULT_FETCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Upgrade-Insecure-Requests": "1",
}

BOT_WALL_MARKERS = (
    b"access to this page has been denied",
    b"access denied",
    b"please verify you are a human",
    b"unusual traffic",
    b"cf-browser-verification",
    b"akamai",
    b"perimeterx",
    b"px-captcha",
)

BLOCKED_HOSTNAMES = frozenset(
    {
        "localhost",
        "metadata.google.internal",
        "169.254.169.254",
        "metadata.azure.com",
    }
)


class UrlFetchError(Exception):
    """Raised when URL fetch is rejected or fails."""


@dataclass
class FetchResult:
    path: Path
    content_type: str
    byte_size: int


class _TimeoutHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS connection with separate connect and read socket timeouts."""

    def __init__(
        self,
        host: str,
        *,
        port: int = 443,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT_SEC,
        read_timeout: float = DEFAULT_READ_TIMEOUT_SEC,
        context: ssl.SSLContext | None = None,
        **kwargs: object,
    ) -> None:
        kwargs.pop("timeout", None)
        kwargs.pop("check_hostname", None)
        super().__init__(host, port=port, timeout=read_timeout, context=context, **kwargs)
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout

    def connect(self) -> None:
        sock = socket.create_connection(
            (self.host, self.port),
            timeout=self._connect_timeout,
        )
        sock.settimeout(self._read_timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


class _TimeoutHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(
        self,
        connect_timeout: float,
        read_timeout: float,
        *,
        context: ssl.SSLContext | None = None,
    ) -> None:
        super().__init__(context=context or ssl.create_default_context())
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout

    def https_open(self, req: urllib.request.Request) -> http.client.HTTPResponse:  # type: ignore[override]
        req.timeout = self._read_timeout

        def connection_factory(
            host: str,
            timeout: float | None = None,
            **http_conn_args: object,
        ) -> _TimeoutHTTPSConnection:
            ctx = http_conn_args.get("context") or self._context
            return _TimeoutHTTPSConnection(
                host,
                connect_timeout=self._connect_timeout,
                read_timeout=float(timeout or self._read_timeout),
                context=ctx,  # type: ignore[arg-type]
            )

        return self.do_open(connection_factory, req, context=self._context)


def _classify_ip(ip_str: str) -> str | None:
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return None
    if addr.is_loopback:
        return "loopback"
    if addr.is_private:
        return "private"
    if addr.is_link_local:
        return "link-local"
    if addr.is_multicast or addr.is_reserved:
        return "reserved"
    if addr == ipaddress.ip_address("169.254.169.254"):
        return "metadata"
    return None


def _resolve_host_ips(hostname: str, *, timeout_sec: float = DEFAULT_DNS_TIMEOUT_SEC) -> list[str]:
    prev = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout_sec)
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise UrlFetchError(f"DNS resolution failed for {hostname}") from exc
    finally:
        socket.setdefaulttimeout(prev)
    ips: list[str] = []
    for info in infos:
        sockaddr = info[4]
        if sockaddr:
            ips.append(sockaddr[0])
    return ips


def validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise UrlFetchError("Only https: URLs are allowed")
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise UrlFetchError("URL missing hostname")
    if hostname in BLOCKED_HOSTNAMES:
        raise UrlFetchError(f"Blocked hostname: {hostname}")
    for ip in _resolve_host_ips(hostname):
        reason = _classify_ip(ip)
        if reason:
            raise UrlFetchError(f"Blocked IP {ip} ({reason}) for host {hostname}")


def _fetch_headers_for_url(url: str) -> dict[str, str]:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    origin = f"{parsed.scheme}://{host}"
    headers = dict(DEFAULT_FETCH_HEADERS)
    headers.update(
        {
            "Referer": origin + "/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
        }
    )
    return headers


def _read_limited_response(response: http.client.HTTPResponse, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = response.read(65536)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise UrlFetchError(f"Response exceeds max size ({max_bytes} bytes)")
        chunks.append(chunk)
    return b"".join(chunks)


def _looks_like_pdf(data: bytes, content_type: str) -> bool:
    if data[:4] == b"%PDF":
        return True
    ct_lower = content_type.lower()
    return "pdf" in ct_lower or "octet-stream" in ct_lower


def _check_bot_wall(data: bytes, content_type: str, *, status: int | None = None) -> None:
    if _looks_like_pdf(data, content_type):
        return
    sample = data[:16384].lower()
    if any(marker in sample for marker in BOT_WALL_MARKERS):
        raise UrlFetchError(
            "Site blocked automated download (bot protection). "
            "Prefer a direct manufacturer PDF URL in the symbol Datasheet field, "
            "manual attach, or AI discovery when available."
        )
    if status == 403:
        raise UrlFetchError(
            "HTTP 403 Forbidden — host blocked this automated request. "
            "Try a direct manufacturer PDF URL or manual attach."
        )
    title_match = re.search(rb"<title[^>]*>([^<]+)</title>", sample, re.I)
    if title_match and b"denied" in title_match.group(1).lower():
        raise UrlFetchError(
            "Site returned an access-denied page instead of a PDF. "
            "Use a direct manufacturer PDF URL or manual attach."
        )


def _warmup_host(
    opener: urllib.request.OpenerDirector,
    url: str,
    *,
    read_timeout: float,
) -> None:
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.hostname}/"
    warmup_req = urllib.request.Request(
        origin,
        headers=_fetch_headers_for_url(origin),
        method="GET",
    )
    try:
        with opener.open(warmup_req, timeout=read_timeout) as response:
            response.read(8192)
    except (urllib.error.URLError, OSError, TimeoutError):
        pass


def _urllib_fetch_bytes(
    url: str,
    *,
    max_bytes: int,
    connect_timeout: float,
    read_timeout: float,
    warmup: bool,
) -> tuple[bytes, str]:
    jar = http.cookiejar.CookieJar()
    handler = _TimeoutHTTPSHandler(connect_timeout, read_timeout)
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar),
        handler,
    )
    if warmup:
        _warmup_host(opener, url, read_timeout=read_timeout)

    request = urllib.request.Request(
        url,
        headers=_fetch_headers_for_url(url),
        method="GET",
    )
    try:
        with opener.open(request, timeout=read_timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            status = getattr(response, "status", None)
            data = _read_limited_response(response, max_bytes)
    except urllib.error.HTTPError as exc:
        body = exc.read(16384) if exc.fp else b""
        _check_bot_wall(body, exc.headers.get("Content-Type", ""), status=exc.code)
        raise UrlFetchError(f"HTTP {exc.code} {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise UrlFetchError(f"Fetch failed: {exc}") from exc
    except OSError as exc:
        raise UrlFetchError(f"Fetch failed: {exc}") from exc

    _check_bot_wall(data, content_type, status=status)
    return data, content_type


def _https_fetch_bytes(
    url: str,
    *,
    headers: dict[str, str],
    max_bytes: int,
    connect_timeout: float,
    read_timeout: float,
) -> tuple[bytes, str]:
    current = url
    context = ssl.create_default_context()

    for _ in range(MAX_REDIRECTS):
        validate_url(current)
        parsed = urlparse(current)
        host = parsed.hostname or ""
        port = parsed.port or 443
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        conn = _TimeoutHTTPSConnection(
            host,
            port=port,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            context=context,
        )
        try:
            conn.request("GET", path, headers={**headers, "Host": host})
            response = conn.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                if not location:
                    raise UrlFetchError(
                        f"Redirect {response.status} missing Location header"
                    )
                current = urljoin(current, location)
                continue
            content_type = response.headers.get("Content-Type", "")
            data = _read_limited_response(response, max_bytes)
            if response.status >= 400:
                _check_bot_wall(data, content_type, status=response.status)
                raise UrlFetchError(
                    f"HTTP {response.status} {response.reason or 'error'}"
                )
            _check_bot_wall(data, content_type, status=response.status)
            return data, content_type
        except OSError as exc:
            raise UrlFetchError(f"Fetch failed: {exc}") from exc
        finally:
            conn.close()

    raise UrlFetchError(f"Too many redirects (>{MAX_REDIRECTS})")


def fetch_url_to_file(
    url: str,
    dest: Path,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    timeout_sec: int = DEFAULT_CONNECT_TIMEOUT_SEC,
    read_timeout_sec: int = DEFAULT_READ_TIMEOUT_SEC,
    warmup: bool = True,
    opener: Callable[..., object] | None = None,
) -> FetchResult:
    """Fetch an HTTPS URL to a local file.

    ``timeout_sec`` is the connect / time-to-response-headers budget (default 10s).
    ``read_timeout_sec`` limits PDF body download time after the server responds.
    """
    validate_url(url)
    dest = dest.expanduser()
    dest.parent.mkdir(parents=True, exist_ok=True)

    if opener is not None:
        request = urllib.request.Request(
            url,
            headers=_fetch_headers_for_url(url),
            method="GET",
        )
        try:
            with opener(request, timeout=float(read_timeout_sec)) as response:  # type: ignore[arg-type]
                content_type = response.headers.get("Content-Type", "")  # type: ignore[union-attr]
                total = 0
                chunks: list[bytes] = []
                while True:
                    chunk = response.read(65536)  # type: ignore[union-attr]
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes:
                        raise UrlFetchError(
                            f"Response exceeds max size ({max_bytes} bytes)"
                        )
                    chunks.append(chunk)
                data = b"".join(chunks)
        except urllib.error.URLError as exc:
            raise UrlFetchError(f"Fetch failed: {exc}") from exc
    elif warmup:
        data, content_type = _urllib_fetch_bytes(
            url,
            max_bytes=max_bytes,
            connect_timeout=float(timeout_sec),
            read_timeout=float(read_timeout_sec),
            warmup=True,
        )
    else:
        try:
            data, content_type = _https_fetch_bytes(
                url,
                headers=_fetch_headers_for_url(url),
                max_bytes=max_bytes,
                connect_timeout=float(timeout_sec),
                read_timeout=float(read_timeout_sec),
            )
        except UrlFetchError:
            raise
        except OSError as exc:
            raise UrlFetchError(f"Fetch failed: {exc}") from exc

    if not _looks_like_pdf(data, content_type):
        _check_bot_wall(data, content_type)
        raise UrlFetchError(
            f"Unexpected content type: {content_type!r} (expected PDF)"
        )
    dest.write_bytes(data)
    return FetchResult(path=dest, content_type=content_type, byte_size=len(data))
