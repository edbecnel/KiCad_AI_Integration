"""Convert User Guide markdown to HTML for wx.html.HtmlWindow."""

from __future__ import annotations

import html
import re
from pathlib import Path

_GUIDE_CSS = """
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: #e8e8e8;
  background: #2d2d2d;
  margin: 12px 16px;
}
h1, h2, h3, h4 { color: #f3f3f3; margin-top: 1.2em; margin-bottom: 0.5em; }
a { color: #6eb6ff; }
code, pre {
  font-family: Menlo, Monaco, Consolas, monospace;
  background: #1e1e1e;
  border-radius: 4px;
}
code { padding: 1px 4px; }
pre {
  padding: 10px 12px;
  overflow-x: auto;
  border: 1px solid #444;
}
pre code { background: transparent; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; }
th, td { border: 1px solid #555; padding: 6px 8px; text-align: left; color: #e8e8e8 !important; }
th { background: #383838 !important; }
td { background: #2d2d2d !important; }
blockquote {
  border-left: 3px solid #666;
  margin: 8px 0;
  padding: 4px 12px;
  color: #cfcfcf;
}
ul, ol { padding-left: 1.4em; }
hr { border: none; border-top: 1px solid #555; margin: 16px 0; }
"""

_SEPARATOR_CELL_RE = re.compile(r"^:?-{3,}:?$")
_HTML_TABLE_RE = re.compile(r"<table\b.*?</table>", re.IGNORECASE | re.DOTALL)
_ORDERED_LIST_RE = re.compile(r"^\d+\.\s+")
# wx.html ignores stylesheet rules; use light cell backgrounds + dark text there.
_WX_TH_BG = "#eeeeee"
_WX_TD_BG = "#ffffff"
_WX_CELL_TEXT = "#1a1a1a"


def markdown_to_html(markdown_text: str, *, title: str = "User Guide") -> str:
    """Render markdown to a full HTML document."""
    body = _convert_body(markdown_text)
    safe_title = html.escape(title)
    return (
        "<!DOCTYPE html><html><head>"
        f"<meta charset='utf-8'><title>{safe_title}</title>"
        f"<style>{_GUIDE_CSS}</style>"
        f"</head><body>{body}</body></html>"
    )


def _convert_body(markdown_text: str) -> str:
    text = _replace_gfm_tables(markdown_text)
    try:
        import markdown  # type: ignore[import-untyped]

        body = markdown.markdown(
            text,
            extensions=["fenced_code", "sane_lists"],
        )
    except ImportError:
        body = _minimal_markdown_to_html(text)
    return _postprocess_for_wxhtml(body)


def _replace_gfm_tables(text: str) -> str:
    """Convert GitHub-style pipe tables to HTML before other markdown processing."""
    lines = text.splitlines()
    out: list[str] = []
    index = 0
    while index < len(lines):
        if _is_table_row(lines[index]):
            end = index + 1
            while end < len(lines) and _is_table_row(lines[end]):
                end += 1
            table_html = _gfm_table_block_to_html(lines[index:end])
            if table_html is not None:
                out.append(table_html)
                index = end
                continue
        out.append(lines[index])
        index += 1
    return "\n".join(out)


def _is_table_row(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and stripped.startswith("|") and stripped.count("|") >= 2


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _separator_alignments(cells: list[str]) -> list[str]:
    alignments: list[str] = []
    for cell in cells:
        token = cell.strip()
        if not _SEPARATOR_CELL_RE.fullmatch(token):
            return []
        if token.startswith(":") and token.endswith(":"):
            alignments.append("center")
        elif token.endswith(":"):
            alignments.append("right")
        else:
            alignments.append("left")
    return alignments


def _gfm_table_block_to_html(lines: list[str]) -> str | None:
    if len(lines) < 2:
        return None
    header_cells = _split_table_row(lines[0])
    if not header_cells:
        return None
    separator_cells = _split_table_row(lines[1])
    alignments = _separator_alignments(separator_cells)
    if not alignments or len(alignments) != len(header_cells):
        return None

    rows = [_split_table_row(line) for line in lines[2:]]
    if any(len(row) != len(header_cells) for row in rows):
        return None

    parts = [
        '<table border="1" cellpadding="6" cellspacing="0" width="100%">',
        "<thead><tr>",
    ]
    for index, cell in enumerate(header_cells):
        align = alignments[index]
        parts.append(
            f'<th align="{align}" bgcolor="{_WX_TH_BG}">'
            f'<font color="{_WX_CELL_TEXT}">{_inline_format(cell)}</font></th>'
        )
    parts.append("</tr></thead><tbody>")
    for row in rows:
        parts.append("<tr>")
        for index, cell in enumerate(row):
            align = alignments[index]
            parts.append(
                f'<td align="{align}" bgcolor="{_WX_TD_BG}">'
                f'<font color="{_WX_CELL_TEXT}">{_inline_format(cell)}</font></td>'
            )
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def _postprocess_for_wxhtml(body: str) -> str:
    """Add wx.html-friendly table attributes when markdown emitted bare tags."""
    if "<table" not in body.lower():
        return body

    def _upgrade_table(match: re.Match[str]) -> str:
        table_html = match.group(0)
        if 'border="' in table_html.lower():
            return table_html
        table_html = re.sub(
            r"<table\b",
            '<table border="1" cellpadding="6" cellspacing="0" width="100%"',
            table_html,
            count=1,
            flags=re.IGNORECASE,
        )
        table_html = re.sub(
            r"<th\b(?![^>]*\bbgcolor=)",
            f'<th bgcolor="{_WX_TH_BG}"',
            table_html,
            flags=re.IGNORECASE,
        )
        table_html = re.sub(
            r"<td\b(?![^>]*\bbgcolor=)",
            f'<td bgcolor="{_WX_TD_BG}"',
            table_html,
            flags=re.IGNORECASE,
        )
        table_html = re.sub(
            r"<th\b([^>]*)>(?!<font\b)",
            rf'<th\1><font color="{_WX_CELL_TEXT}">',
            table_html,
            flags=re.IGNORECASE,
        )
        table_html = re.sub(
            r"</th>",
            "</font></th>",
            table_html,
            flags=re.IGNORECASE,
        )
        table_html = re.sub(
            r"<td\b([^>]*)>(?!<font\b)",
            rf'<td\1><font color="{_WX_CELL_TEXT}">',
            table_html,
            flags=re.IGNORECASE,
        )
        table_html = re.sub(
            r"</td>",
            "</font></td>",
            table_html,
            flags=re.IGNORECASE,
        )
        return table_html

    return _HTML_TABLE_RE.sub(_upgrade_table, body)


def _minimal_markdown_to_html(text: str) -> str:
    """Small fallback when the ``markdown`` package is not installed."""
    parts = re.split(r"(<table\b.*?</table>)", text, flags=re.IGNORECASE | re.DOTALL)
    chunks: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.lower().startswith("<table"):
            chunks.append(part)
        else:
            chunks.append(_minimal_markdown_fragment(part))
    return "".join(chunks)


def _minimal_markdown_fragment(text: str) -> str:
    lines = text.splitlines()
    chunks: list[str] = []
    paragraph: list[str] = []
    in_code = False
    code_lines: list[str] = []
    index = 0

    def flush_paragraph() -> None:
        if not paragraph:
            return
        joined = " ".join(paragraph).strip()
        if joined:
            chunks.append(f"<p>{_inline_format(joined)}</p>")
        paragraph.clear()

    while index < len(lines):
        line = lines[index].rstrip()
        if line.strip().startswith("```"):
            if in_code:
                chunks.append(
                    "<pre><code>"
                    + html.escape("\n".join(code_lines))
                    + "</code></pre>"
                )
                code_lines.clear()
                in_code = False
            else:
                flush_paragraph()
                in_code = True
            index += 1
            continue
        if in_code:
            code_lines.append(line)
            index += 1
            continue
        if not line.strip():
            flush_paragraph()
            index += 1
            continue
        if line.startswith("#### "):
            flush_paragraph()
            chunks.append(f"<h4>{html.escape(line[5:])}</h4>")
        elif line.startswith("### "):
            flush_paragraph()
            chunks.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("## "):
            flush_paragraph()
            chunks.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("# "):
            flush_paragraph()
            chunks.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif _ORDERED_LIST_RE.match(line.strip()):
            flush_paragraph()
            list_items: list[str] = []
            while index < len(lines):
                current = lines[index].rstrip()
                if not _ORDERED_LIST_RE.match(current.strip()):
                    break
                item_text = _ORDERED_LIST_RE.sub("", current.strip(), count=1)
                list_items.append(_inline_format(item_text))
                index += 1
            chunks.append("<ol>" + "".join(f"<li>{item}</li>" for item in list_items) + "</ol>")
            continue
        elif line.startswith("- "):
            flush_paragraph()
            chunks.append(f"<ul><li>{_inline_format(line[2:])}</li></ul>")
        else:
            paragraph.append(line)
        index += 1
    flush_paragraph()
    if in_code and code_lines:
        chunks.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
    return "\n".join(chunks)


def _inline_format(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    return escaped


def write_temp_html(html_document: str, *, prefix: str = "kicad_ai_user_guide_") -> Path:
    """Write rendered HTML to a temp file for Open in Browser."""
    import tempfile

    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".html",
        prefix=prefix,
        delete=False,
    )
    with handle:
        handle.write(html_document)
    return Path(handle.name)
