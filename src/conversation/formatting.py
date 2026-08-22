"""Lightweight markdown-to-plain-text formatting for wx text controls."""

from __future__ import annotations

import re


def format_markdown_for_display(text: str) -> str:
    """
    Convert common markdown constructs to readable plain text for TextCtrl display.

    Headings become uppercase lines; bold/italic markers are stripped; fenced code
    blocks are indented.
    """
    lines = text.splitlines()
    out: list[str] = []
    in_code = False
    code_lines: list[str] = []

    def flush_code() -> None:
        nonlocal code_lines
        if not code_lines:
            return
        out.append("")
        for line in code_lines:
            out.append(f"    {line}")
        out.append("")
        code_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                in_code = False
                flush_code()
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            title = _inline_markdown(heading.group(2).strip())
            out.append(title.upper())
            out.append("-" * min(len(title), 60))
            continue

        if stripped.startswith(("- ", "* ")):
            out.append(f"• {_inline_markdown(stripped[2:])}")
            continue

        out.append(_inline_markdown(line))

    if in_code and code_lines:
        flush_code()

    return "\n".join(out).strip("\n")


def _inline_markdown(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text
