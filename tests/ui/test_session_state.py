"""Tests for session state normalization."""

from __future__ import annotations

from ui.session_state import normalize_tab_session_block


def test_normalize_chat_block_flat() -> None:
    flat = {"template": "general_review", "question_draft": "Why D1?"}
    assert normalize_tab_session_block(flat, nested_key="chat") == flat


def test_normalize_chat_block_question_alias() -> None:
    flat = {"template": "general_review", "question": "legacy key"}
    assert normalize_tab_session_block(flat, nested_key="chat") == flat


def test_normalize_chat_block_legacy_nested() -> None:
    inner = {"design_intent": "flyback", "question_draft": "trace D1"}
    wrapped = {"chat": inner}
    assert normalize_tab_session_block(wrapped, nested_key="chat") == inner
