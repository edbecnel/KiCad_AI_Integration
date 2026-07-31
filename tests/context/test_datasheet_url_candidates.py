"""Tests for datasheet URL heuristics and quality filters."""

from __future__ import annotations

from unittest.mock import patch

from context.ai_datasheet_discovery import _validate_suggested_urls
from context.datasheet_url_candidates import (
    heuristic_datasheet_urls,
    merge_url_candidates,
    reject_datasheet_url,
)


def test_reject_onsemi_portal_not_found_url() -> None:
    bad = "https://www.onsemi.com/design/technical-documentation?notFound=bd243-d.pdf"
    assert reject_datasheet_url(bad) is not None


def test_reject_non_pdf_url() -> None:
    assert reject_datasheet_url("https://www.onsemi.com/products/bd243c") is not None


def test_accept_onsemi_direct_pdf() -> None:
    good = "https://www.onsemi.com/download/data-sheet/pdf/bd243b-d.pdf"
    assert reject_datasheet_url(good) is None


def test_heuristic_bd243c_includes_family_b_variant() -> None:
    urls = heuristic_datasheet_urls("BD243C", {})
    assert "https://www.onsemi.com/download/data-sheet/pdf/bd243c-d.pdf" in urls
    assert "https://www.onsemi.com/download/data-sheet/pdf/bd243b-d.pdf" in urls


def test_validate_suggested_urls_filters_portal() -> None:
    portal = "https://www.onsemi.com/design/technical-documentation?notFound=bd243-d.pdf"
    direct = "https://www.onsemi.com/download/data-sheet/pdf/bd243b-d.pdf"
    with patch("context.ai_datasheet_discovery.validate_url"):
        valid = _validate_suggested_urls([portal, direct])
    assert valid == [direct]


def test_merge_url_candidates_preserves_order() -> None:
    first = ["https://example.com/a.pdf", "https://example.com/b.pdf"]
    second = ["https://example.com/b.pdf", "https://example.com/c.pdf"]
    assert merge_url_candidates(first, second) == [
        "https://example.com/a.pdf",
        "https://example.com/b.pdf",
        "https://example.com/c.pdf",
    ]
