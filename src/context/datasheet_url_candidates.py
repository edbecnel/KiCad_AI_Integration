"""Heuristic datasheet PDF URL candidates and quality filters for AI discovery."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

# Portal / search pages that are never direct PDF downloads.
_BAD_URL_SUBSTRINGS = (
    "notfound=",
    "/design/technical-documentation",
    "/products/product/",
    "/search?",
    "/parametric/",
    "octopart.com",
    "findchips.com",
)

# Paths that look like HTML product pages (not terminal .pdf).
_BAD_PATH_SUFFIXES = (
    ".html",
    ".htm",
    ".aspx",
    ".php",
)


def reject_datasheet_url(url: str) -> str | None:
    """Return a rejection reason, or None if the URL looks like a direct PDF link."""
    cleaned = url.strip()
    if not cleaned:
        return "empty URL"
    parsed = urlparse(cleaned)
    path = (parsed.path or "").lower()
    if not path.endswith(".pdf"):
        return "URL must end with .pdf (not a portal or HTML page)"
    lowered = cleaned.lower()
    for marker in _BAD_URL_SUBSTRINGS:
        if marker in lowered:
            return f"URL looks like a search/portal page ({marker})"
    for suffix in _BAD_PATH_SUFFIXES:
        if path.endswith(suffix):
            return f"URL path ends with {suffix}"
    return None


def _infer_manufacturer_hosts(symbol_context: dict[str, Any]) -> set[str]:
    hosts: set[str] = set()
    symbol_url = symbol_context.get("symbol_datasheet_url")
    if isinstance(symbol_url, str) and symbol_url.startswith("https://"):
        host = (urlparse(symbol_url).hostname or "").lower()
        if host:
            hosts.add(host)
            if host.endswith("onsemi.com"):
                hosts.add("onsemi.com")
    custom = symbol_context.get("custom_fields")
    if isinstance(custom, dict):
        for key in ("Manufacturer", "manufacturer", "Mfr", "mfr"):
            val = custom.get(key)
            if isinstance(val, str):
                mfr = val.lower()
                if "onsemi" in mfr or "fairchild" in mfr:
                    hosts.add("onsemi.com")
                if "texas instruments" in mfr or mfr in ("ti", "ti.com"):
                    hosts.add("ti.com")
                if "stmicro" in mfr or mfr in ("st", "st.com"):
                    hosts.add("st.com")
    lib_id = symbol_context.get("lib_id")
    if isinstance(lib_id, str):
        lib_lower = lib_id.lower()
        if "onsemi" in lib_lower or "fairchild" in lib_lower:
            hosts.add("onsemi.com")
    return hosts


def _onsemi_candidates(part: str) -> list[str]:
    """onsemi direct PDF pattern used across Fairchild / onsemi discrete parts."""
    base = "https://www.onsemi.com/download/data-sheet/pdf"
    part_upper = part.strip().upper()
    if not part_upper:
        return []
    candidates = [f"{base}/{part_upper.lower()}-d.pdf"]
    # Family datasheets often use the 'B' grade document (e.g. BD243C → bd243b-d.pdf).
    family = re.match(r"^([A-Z]{2,}\d+)([A-Z])$", part_upper)
    if family:
        stem, suffix = family.group(1), family.group(2)
        if suffix != "B":
            candidates.append(f"{base}/{stem.lower()}b-d.pdf")
    return candidates


def _ti_candidates(part: str) -> list[str]:
    part_upper = part.strip().upper()
    if not part_upper:
        return []
    return [f"https://www.ti.com/lit/ds/symlink/{part_upper.lower()}.pdf"]


def _st_candidates(part: str) -> list[str]:
    part_upper = part.strip().upper()
    if not part_upper:
        return []
    return [
        f"https://www.st.com/resource/en/datasheet/{part_upper.lower()}.pdf",
    ]


def heuristic_datasheet_urls(part: str, symbol_context: dict[str, Any]) -> list[str]:
    """
    Generate ordered direct-PDF URL guesses from part number and symbol metadata.

    These are tried before AI suggestions because models often hallucinate portal URLs.
    """
    part_norm = part.strip()
    if not part_norm:
        return []
    hosts = _infer_manufacturer_hosts(symbol_context)
    candidates: list[str] = []

    # Always include onsemi patterns for classic discrete prefixes when unknown or onsemi.
    onsemi_prefixes = ("BD", "BU", "FOD", "MMBT", "MPS", "NCP", "NCV", "TIP", "2N")
    if not hosts or "onsemi.com" in hosts or part_norm.upper().startswith(onsemi_prefixes):
        candidates.extend(_onsemi_candidates(part_norm))

    if "ti.com" in hosts:
        candidates.extend(_ti_candidates(part_norm))
    if "st.com" in hosts:
        candidates.extend(_st_candidates(part_norm))

    return merge_url_candidates(candidates)


def merge_url_candidates(*lists: list[str]) -> list[str]:
    """Dedupe URLs preserving first-seen order."""
    merged: list[str] = []
    seen: set[str] = set()
    for urls in lists:
        for url in urls:
            key = url.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(key)
    return merged
