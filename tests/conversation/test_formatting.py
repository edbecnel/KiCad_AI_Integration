"""Tests for conversation display formatting."""

from __future__ import annotations

from pathlib import Path

from conversation.formatting import (
    conversation_log_to_markdown,
    format_markdown_for_display,
    format_session_as_markdown,
    normalize_message_markdown,
)
from conversation.pricing import estimate_cost_usd
from conversation.session import ChatSession


def test_format_markdown_for_display_headings_and_bold() -> None:
    text = "## Summary\n\nThis is **important**."
    rendered = format_markdown_for_display(text)
    assert "SUMMARY" in rendered
    assert "important" in rendered
    assert "**" not in rendered


def test_format_markdown_for_display_code_fence() -> None:
    text = "```\nline one\nline two\n```"
    rendered = format_markdown_for_display(text)
    assert "    line one" in rendered
    assert "```" not in rendered


def test_estimate_cost_usd_known_model() -> None:
    cost = estimate_cost_usd("claude-3-5-sonnet-20241022", 1000, 500)
    assert cost is not None
    assert cost > 0


def test_normalize_ascii_table_to_pipe_markdown() -> None:
    text = "Ref    Value\nQ1     BD243C\nT1     Coil"
    md = normalize_message_markdown(text)
    assert "| Ref | Value |" in md
    assert "| Q1 | BD243C |" in md


def test_conversation_log_to_markdown_roles() -> None:
    log = "--- You ---\nWhat is Q1?\n\n--- Assistant ---\nSUMMARY\n-----\n**Done**."
    md = conversation_log_to_markdown(log)
    assert "## You" in md
    assert "## Assistant" in md
    assert "## Summary" in md
    assert "**Done**" in md


def test_format_session_as_markdown_preserves_assistant_markdown() -> None:
    session = ChatSession(project_path=Path("/tmp/bedini.kicad_pro"))
    session.append_user("Explain Q1")
    session.append_assistant("## Analysis\n\n| Ref | Part |\n| --- | --- |\n| Q1 | BD243C |")
    md = format_session_as_markdown(session)
    assert "# KiCad AI — bedini" in md
    assert "## You" in md
    assert "## Assistant" in md
    assert "| Q1 | BD243C |" in md


def test_format_conversation_log_includes_tokens_and_cost() -> None:
    session = ChatSession(project_path=Path("/tmp/a.kicad_pro"))
    session.append_user("question")
    session.append_assistant(
        "**Answer**",
        input_tokens=100,
        output_tokens=50,
        model="claude-3-5-sonnet-20241022",
    )
    log = session.format_conversation_log()
    assert "100 in, 50 out tokens" in log
    assert "~$" in log
    assert "ANSWER" in log or "Answer" in log
