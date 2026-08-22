"""Tests for Assistant shell UI preferences."""

from __future__ import annotations

from pathlib import Path

from ui import shell_preferences


def test_shell_preferences_last_tab_round_trip(tmp_path: Path, monkeypatch) -> None:
    prefs = tmp_path / "prefs.json"
    monkeypatch.setattr(shell_preferences, "_PREFS_PATH", prefs)
    pro = tmp_path / "board.kicad_pro"

    assert shell_preferences.get_last_tab(pro) is None
    shell_preferences.set_last_tab(pro, "simulation")
    assert shell_preferences.get_last_tab(pro) == "simulation"
