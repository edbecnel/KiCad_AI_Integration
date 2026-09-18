"""Tests for Assistant session persistence."""

from __future__ import annotations

from pathlib import Path

from ui.assistant_session import (
    SESSION_VERSION,
    load_session,
    save_session,
    session_path_for_project,
)


def test_session_path_for_kicad_pro(tmp_path: Path) -> None:
    pro = tmp_path / "board.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    assert session_path_for_project(pro) == tmp_path / "kicad_ai" / "assistant_session.json"


def test_save_and_load_session_round_trip(tmp_path: Path) -> None:
    pro = tmp_path / "board.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    payload = {
        "active_tab": "chat",
        "tabs": {"chat": {"chat": {"template": "general_review"}}},
    }
    path = save_session(pro, payload)
    assert path.is_file()
    loaded = load_session(pro)
    assert loaded is not None
    assert loaded["version"] == SESSION_VERSION
    assert loaded["active_tab"] == "chat"
    assert loaded["tabs"]["chat"]["chat"]["template"] == "general_review"
