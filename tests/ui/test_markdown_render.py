"""Tests for user guide markdown rendering."""

from __future__ import annotations

from ui.markdown_render import (
    _convert_body,
    _gfm_table_block_to_html,
    _replace_gfm_tables,
    markdown_to_html,
)

SAMPLE_TABLE = """| Goal | Read in order |
|------|----------------|
| **New user** | [Getting Started](00_Getting_Started.md) |
| PCB layout | Audits → Routing |
"""


def test_markdown_to_html_includes_heading_and_code() -> None:
    html_doc = markdown_to_html("# Hello\n\nUse `Refresh context`.\n", title="Test")
    assert "<h1" in html_doc
    assert "Hello" in html_doc
    assert "<code" in html_doc or "Refresh context" in html_doc
    assert "<style>" in html_doc


def test_markdown_to_html_renders_link() -> None:
    html_doc = markdown_to_html("[Chat](02_Chat.md)", title="Test")
    assert 'href="02_Chat.md"' in html_doc


def test_gfm_table_block_to_html_renders_cells() -> None:
    lines = SAMPLE_TABLE.strip().splitlines()
    table_html = _gfm_table_block_to_html(lines)
    assert table_html is not None
    assert "<table" in table_html
    assert "<th" in table_html
    assert "<td" in table_html
    assert 'bgcolor="#eeeeee"' in table_html
    assert 'color="#1a1a1a"' in table_html
    assert "Goal" in table_html
    assert "Getting Started" in table_html
    assert "<strong>New user</strong>" in table_html
    assert "|" not in table_html


def test_replace_gfm_tables_converts_pipe_syntax() -> None:
    converted = _replace_gfm_tables(SAMPLE_TABLE)
    assert "<table" in converted
    assert "| Goal |" not in converted


def test_convert_body_renders_tables_without_markdown_package(monkeypatch) -> None:
    import builtins

    real_import = builtins.__import__

    def _block_markdown(name, *args, **kwargs):
        if name == "markdown":
            raise ImportError("blocked for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block_markdown)
    body = _convert_body(SAMPLE_TABLE)
    assert "<table" in body
    assert "<td" in body
    assert "Getting Started" in body
    assert "|------|" not in body


def test_convert_body_renders_tables_with_markdown_package() -> None:
    pytest = __import__("pytest")
    markdown = pytest.importorskip("markdown")
    if markdown is None:
        pytest.skip("markdown package not installed")
    body = _convert_body(SAMPLE_TABLE)
    assert "<table" in body
    assert "Getting Started" in body
    assert "|------|" not in body


def test_convert_body_renders_ordered_lists_without_markdown_package(monkeypatch) -> None:
    import builtins

    real_import = builtins.__import__

    def _block_markdown(name, *args, **kwargs):
        if name == "markdown":
            raise ImportError("blocked for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block_markdown)
    sample = """### 1. View AERF results

1. **Refresh context** after **Write to EKM…**
2. Open **Notebook** (Ctrl+5).
3. Expand sections.
"""
    body = _convert_body(sample)
    assert "<ol>" in body
    assert "<li>" in body
    assert body.count("<li>") >= 3
    assert "Refresh context" in body
    assert "Open <strong>Notebook</strong>" in body or "Notebook" in body
    assert "1. **Refresh context** 2. Open" not in body
