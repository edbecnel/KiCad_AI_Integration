"""Tests for conversation display formatting."""

from __future__ import annotations

from pathlib import Path

from conversation.formatting import format_markdown_for_display
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
