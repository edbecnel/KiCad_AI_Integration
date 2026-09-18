"""Conversation display formatting and markdown export."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from conversation.session import ChatSession


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


_ROLE_LINE = re.compile(r"^---\s*(You|Assistant)\s*---\s*$", re.I)
_META_LINE = re.compile(r"^\[[^\]]+\]\s*$")
_TABLE_CELL_SPLIT = re.compile(r"\s{2,}|\t")
_ATX_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def format_session_as_markdown(session: ChatSession) -> str:
    """Export full session with original assistant markdown preserved."""
    from conversation.session import ChatRole

    project = session.project_path.stem
    lines: list[str] = [
        f"# KiCad AI — {project}",
        "",
        f"_Project: `{session.project_path}`_",
        "",
    ]
    for turn in session.turns:
        role = "You" if turn.role is ChatRole.USER else "Assistant"
        lines.extend(["---", "", f"## {role}", ""])
        if turn.timestamp:
            lines.append(f"_{turn.timestamp}_")
            lines.append("")
        lines.append(normalize_message_markdown(turn.text))
        if turn.role is ChatRole.ASSISTANT and (
            turn.input_tokens is not None or turn.output_tokens is not None
        ):
            meta: list[str] = []
            if turn.input_tokens is not None and turn.output_tokens is not None:
                meta.append(f"{turn.input_tokens} in / {turn.output_tokens} out tokens")
            if turn.model:
                meta.append(turn.model)
            from conversation.pricing import estimate_cost_usd

            cost = estimate_cost_usd(turn.model, turn.input_tokens, turn.output_tokens)
            if cost is not None:
                meta.append(f"~${cost:.4f}")
            if meta:
                lines.extend(["", f"*{' · '.join(meta)}*"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def conversation_log_to_markdown(log: str) -> str:
    """Best-effort markdown export from the plain-text conversation log."""
    text = log.strip()
    if not text:
        return ""
    if text.startswith("(No messages yet"):
        return ""
    blocks: list[tuple[str, str]] = []
    current_role = ""
    current_lines: list[str] = []
    for line in text.splitlines():
        role_match = _ROLE_LINE.match(line.strip())
        if role_match:
            if current_role:
                blocks.append((current_role, "\n".join(current_lines).strip()))
            current_role = role_match.group(1).title()
            if current_role.lower() == "you":
                current_role = "You"
            else:
                current_role = "Assistant"
            current_lines = []
            continue
        if _META_LINE.match(line.strip()):
            current_lines.append(line.strip())
            continue
        current_lines.append(line)
    if current_role:
        blocks.append((current_role, "\n".join(current_lines).strip()))

    if not blocks:
        return normalize_message_markdown(text) + "\n"

    out: list[str] = ["# KiCad AI conversation", ""]
    for role, body in blocks:
        out.extend(["---", "", f"## {role}", ""])
        body_lines = body.splitlines()
        cleaned: list[str] = []
        for raw in body_lines:
            if _META_LINE.match(raw.strip()):
                inner = raw.strip()[1:-1]
                cleaned.append(f"*{inner}*")
            else:
                cleaned.append(raw)
        out.append(normalize_message_markdown("\n".join(cleaned), from_display=True))
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def normalize_message_markdown(text: str, *, from_display: bool = False) -> str:
    """Normalize plain or mixed text into readable markdown."""
    if not text.strip():
        return ""
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    in_fence = False
    fence_lines: list[str] = []

    def flush_fence() -> None:
        nonlocal fence_lines
        if not fence_lines:
            return
        out.append("```")
        out.extend(fence_lines)
        out.append("```")
        fence_lines = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_fence:
                in_fence = False
                flush_fence()
            else:
                in_fence = True
            i += 1
            continue
        if in_fence:
            fence_lines.append(line)
            i += 1
            continue

        if _ATX_HEADING.match(line):
            level, title = _ATX_HEADING.match(line).groups()  # type: ignore[union-attr]
            out.append(f"{level} {_normalize_inline_markdown(title)}")
            i += 1
            continue

        if from_display and i + 1 < len(lines) and _is_underline_heading(stripped, lines[i + 1]):
            title = _display_title_to_heading(stripped)
            out.append(title)
            i += 2
            continue

        if _is_horizontal_rule_line(stripped):
            out.append("---")
            i += 1
            continue

        table_block, next_i = _consume_markdown_or_ascii_table(lines, i)
        if table_block is not None:
            out.extend(table_block)
            i = next_i
            continue

        if stripped.startswith("• "):
            out.append(f"- {_normalize_inline_markdown(stripped[2:])}")
            i += 1
            continue
        if stripped.startswith(("- ", "* ", "+ ")):
            out.append(f"- {_normalize_inline_markdown(stripped[2:])}")
            i += 1
            continue

        numbered = re.match(r"^(\d+)[.)]\s+(.*)$", stripped)
        if numbered:
            out.append(f"{numbered.group(1)}. {_normalize_inline_markdown(numbered.group(2))}")
            i += 1
            continue

        out.append(_normalize_inline_markdown(line))
        i += 1

    if in_fence and fence_lines:
        flush_fence()
    return "\n".join(out).strip("\n")


def _normalize_inline_markdown(text: str) -> str:
    """Normalize underscore-bold to asterisk-bold; keep existing ``**`` markers."""
    if not text:
        return text
    return re.sub(r"__(.+?)__", r"**\1**", text)


def _is_horizontal_rule_line(stripped: str) -> bool:
    if len(stripped) < 3:
        return False
    if stripped in ("---", "***", "___"):
        return True
    return bool(re.fullmatch(r"[-_=~]{3,}", stripped))


def _is_underline_heading(title: str, underline: str) -> bool:
    if not title or title.startswith("#"):
        return False
    if _ROLE_LINE.match(title):
        return False
    return _is_horizontal_rule_line(underline.strip())


def _display_title_to_heading(title: str) -> str:
    cleaned = title.strip()
    if cleaned.isupper() and len(cleaned) > 3:
        cleaned = cleaned.title()
    if cleaned.endswith(":"):
        cleaned = cleaned[:-1]
    return f"## {cleaned}"


def _consume_markdown_or_ascii_table(
    lines: list[str],
    start: int,
) -> tuple[list[str] | None, int]:
    if "|" in lines[start]:
        block: list[str] = []
        i = start
        while i < len(lines) and "|" in lines[i]:
            block.append(lines[i].rstrip())
            i += 1
        return _normalize_pipe_table_block(block), i

    block = []
    i = start
    while i < len(lines) and lines[i].strip() and _TABLE_CELL_SPLIT.search(lines[i]):
        if _ATX_HEADING.match(lines[i]) or _is_horizontal_rule_line(lines[i].strip()):
            break
        block.append(lines[i])
        i += 1
    if len(block) >= 2:
        converted = _ascii_block_to_pipe_table(block)
        if converted is not None:
            return converted, i
    return None, start


def _normalize_pipe_table_block(block: list[str]) -> list[str]:
    rows: list[list[str]] = []
    for line in block:
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        rows.append(parts)
    if not rows:
        return block
    ncol = max(len(r) for r in rows)
    if ncol < 2:
        return block
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    if len(rows) >= 2 and all(re.fullmatch(r":?-+:?", c) for c in rows[1]):
        header, sep, body = rows[0], rows[1], rows[2:]
    else:
        header, sep, body = rows[0], ["---"] * ncol, rows[1:]
    md = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for row in body:
        md.append("| " + " | ".join(row) + " |")
    return md


def _ascii_block_to_pipe_table(block: list[str]) -> list[str] | None:
    rows: list[list[str]] = []
    for line in block:
        cells = [c.strip() for c in _TABLE_CELL_SPLIT.split(line.strip()) if c.strip()]
        if not cells:
            return None
        rows.append(cells)
    if len(rows) < 2:
        return None
    ncol = max(len(r) for r in rows)
    if ncol < 2:
        return None
    if len({len(r) for r in rows}) != 1:
        return None
    md = [
        "| " + " | ".join(rows[0]) + " |",
        "| " + " | ".join(["---"] * ncol) + " |",
    ]
    for row in rows[1:]:
        md.append("| " + " | ".join(row) + " |")
    return md
