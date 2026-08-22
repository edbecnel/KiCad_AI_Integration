"""Tests for conversation session model."""

from __future__ import annotations

from pathlib import Path

from conversation.session import ChatRole, ChatSession, ChatTurn


def test_chat_session_append_and_api_messages() -> None:
    session = ChatSession(project_path=Path("/tmp/test.kicad_pro"))
    session.append_user("What is U3?", api_content="FULL PROMPT")
    session.append_assistant("U3 is a regulator.", input_tokens=10, output_tokens=5)

    assert session.user_turn_count == 1
    assert len(session.turns) == 2
    messages = session.to_api_messages()
    assert messages == [
        {"role": "user", "content": "FULL PROMPT"},
        {"role": "assistant", "content": "U3 is a regulator."},
    ]


def test_chat_session_clear_and_format_log() -> None:
    session = ChatSession(project_path=Path("/tmp/test.kicad_pro"))
    session.append_user("Hello")
    session.append_assistant("Hi there")
    log = session.format_conversation_log()
    assert "--- You ---" in log
    assert "Hello" in log
    assert "--- Assistant ---" in log
    assert "Hi there" in log

    session.clear()
    assert session.turns == []
    assert session.format_conversation_log() == ""


def test_chat_turn_api_text_prefers_api_content() -> None:
    turn = ChatTurn(role=ChatRole.USER, text="short", api_content="long prompt")
    assert turn.api_text() == "long prompt"
