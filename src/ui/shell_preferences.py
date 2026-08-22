"""Persisted Assistant shell UI preferences (last tab per project)."""

from __future__ import annotations

import json
from pathlib import Path

_PREFS_PATH = Path.home() / "kicad_ai_shell_prefs.json"


def _load() -> dict[str, object]:
    if not _PREFS_PATH.is_file():
        return {}
    try:
        with _PREFS_PATH.open(encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save(data: dict[str, object]) -> None:
    with _PREFS_PATH.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def _project_key(project_path: Path | str) -> str:
    return str(Path(project_path).expanduser().resolve())


def get_last_tab(project_path: Path | str) -> str | None:
    """Return the last-selected tab id for a project, if saved."""
    data = _load()
    last_tabs = data.get("last_tab_by_project")
    if not isinstance(last_tabs, dict):
        return None
    value = last_tabs.get(_project_key(project_path))
    return str(value) if value else None


def set_last_tab(project_path: Path | str, tab_id: str) -> None:
    """Remember the selected tab for a project."""
    data = _load()
    last_tabs = data.get("last_tab_by_project")
    if not isinstance(last_tabs, dict):
        last_tabs = {}
    last_tabs[_project_key(project_path)] = tab_id
    data["last_tab_by_project"] = last_tabs
    _save(data)
