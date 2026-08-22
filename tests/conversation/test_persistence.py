"""Tests for conversation disk persistence."""

from __future__ import annotations

from pathlib import Path

from conversation.session import ChatRole
from conversation.store import SessionStore, conversation_file_path, get_session_store


def test_conversation_file_path_under_project_root(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    assert conversation_file_path(pro) == tmp_path / "kicad_ai" / "conversation.json"


def test_session_store_persists_and_reloads(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    pro.write_text("{}", encoding="utf-8")

    store = SessionStore()
    session = store.get_or_create(pro)
    session.append_user("hello")
    session.append_assistant(
        "hi",
        input_tokens=10,
        output_tokens=5,
        model="claude-3-5-sonnet-20241022",
    )
    store.save(pro)

    reloaded_store = SessionStore()
    reloaded = reloaded_store.get_or_create(pro)
    assert len(reloaded.turns) == 2
    assert reloaded.turns[0].role is ChatRole.USER
    assert reloaded.turns[1].text == "hi"
    assert reloaded.turns[1].input_tokens == 10


def test_session_store_reset_clears_disk(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    pro.write_text("{}", encoding="utf-8")

    store = SessionStore()
    store.get_or_create(pro).append_user("one")
    store.save(pro)
    assert conversation_file_path(pro).is_file()

    store.reset(pro)
    reloaded = SessionStore().get_or_create(pro)
    assert reloaded.turns == []


def test_get_session_store_returns_singleton() -> None:
    assert get_session_store() is get_session_store()
