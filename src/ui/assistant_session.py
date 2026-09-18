"""Persist Assistant shell UI choices per KiCad project."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ekm.paths import EKM_DIR_NAME

SESSION_VERSION = 1
SESSION_FILENAME = "assistant_session.json"


def session_path_for_project(project_path: Path | str) -> Path:
    """``<project>/kicad_ai/assistant_session.json``."""
    pro = Path(project_path).expanduser().resolve()
    if pro.suffix == ".kicad_pro":
        base = pro.parent
    elif pro.is_dir():
        base = pro
    else:
        base = pro.parent
    return base / EKM_DIR_NAME / SESSION_FILENAME


def load_session(project_path: Path | str) -> dict[str, Any] | None:
    path = session_path_for_project(project_path)
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if int(data.get("version", 0)) != SESSION_VERSION:
        return None
    return data


def save_session(project_path: Path | str, payload: dict[str, Any]) -> Path:
    path = session_path_for_project(project_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "version": SESSION_VERSION,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    with path.open("w", encoding="utf-8") as fh:
        json.dump(body, fh, indent=2)
        fh.write("\n")
    return path


def load_session_file(path: Path | str) -> dict[str, Any] | None:
    p = Path(path).expanduser()
    if not p.is_file():
        return None
    try:
        with p.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if int(data.get("version", 0)) != SESSION_VERSION:
        return None
    return data


def save_session_file(path: Path | str, payload: dict[str, Any]) -> Path:
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "version": SESSION_VERSION,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    with p.open("w", encoding="utf-8") as fh:
        json.dump(body, fh, indent=2)
        fh.write("\n")
    return p
