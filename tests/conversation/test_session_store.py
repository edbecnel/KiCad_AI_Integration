"""Tests for conversation session store."""

from __future__ import annotations

from pathlib import Path

from conversation.store import SessionStore


def test_session_store_get_or_create_and_reset() -> None:
    store = SessionStore()
    pro = Path("/tmp/a.kicad_pro")
    first = store.get_or_create(pro)
    second = store.get_or_create(pro)
    assert first is second

    first.append_user("one")
    reset = store.reset(pro)
    assert reset is not first
    assert reset.turns == []
    assert store.get(pro) is reset
