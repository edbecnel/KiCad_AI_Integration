"""In-memory chat session store keyed by project path with optional disk persistence."""

from __future__ import annotations

import json
from pathlib import Path

from conversation.session import ChatRole, ChatSession, ChatTurn

_DEFAULT_STORE: "SessionStore | None" = None


def conversation_file_path(project_path: Path | str) -> Path:
    """Return ``<project_root>/kicad_ai/conversation.json`` for a .kicad_pro path."""
    pro = Path(project_path).expanduser().resolve()
    return pro.parent / "kicad_ai" / "conversation.json"


def get_session_store() -> "SessionStore":
    """Return the process-wide session store (shared across UI panels)."""
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = SessionStore()
    return _DEFAULT_STORE


class SessionStore:
    """Holds one ``ChatSession`` per resolved project path."""

    def __init__(self, *, persist: bool = True) -> None:
        self._sessions: dict[str, ChatSession] = {}
        self._persist = persist

    @staticmethod
    def _key(project_path: Path | str) -> str:
        return str(Path(project_path).expanduser().resolve())

    def get_or_create(self, project_path: Path | str) -> ChatSession:
        key = self._key(project_path)
        if key not in self._sessions:
            loaded = self._load_from_disk(Path(key))
            self._sessions[key] = loaded or ChatSession(project_path=Path(key))
        return self._sessions[key]

    def reset(self, project_path: Path | str) -> ChatSession:
        key = self._key(project_path)
        session = ChatSession(project_path=Path(key))
        self._sessions[key] = session
        if self._persist:
            self._save_to_disk(session)
        return session

    def get(self, project_path: Path | str) -> ChatSession | None:
        return self._sessions.get(self._key(project_path))

    def save(self, project_path: Path | str) -> None:
        """Persist the current session for a project to disk."""
        session = self.get(project_path)
        if session is not None and self._persist:
            self._save_to_disk(session)

    def _load_from_disk(self, project_path: Path) -> ChatSession | None:
        path = conversation_file_path(project_path)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(data, dict):
            return None
        turns_raw = data.get("turns")
        if not isinstance(turns_raw, list):
            return None
        turns: list[ChatTurn] = []
        for item in turns_raw:
            if not isinstance(item, dict):
                continue
            role_raw = item.get("role")
            text = item.get("text")
            if role_raw not in {ChatRole.USER.value, ChatRole.ASSISTANT.value}:
                continue
            if not isinstance(text, str):
                continue
            turns.append(
                ChatTurn(
                    role=ChatRole(role_raw),
                    text=text,
                    timestamp=str(item.get("timestamp", "")),
                    api_content=item.get("api_content"),
                    input_tokens=item.get("input_tokens"),
                    output_tokens=item.get("output_tokens"),
                    model=item.get("model"),
                ),
            )
        return ChatSession(project_path=project_path, turns=turns)

    def _save_to_disk(self, session: ChatSession) -> None:
        path = conversation_file_path(session.project_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "project_path": str(session.project_path),
            "turns": [
                {
                    "role": turn.role.value,
                    "text": turn.text,
                    "timestamp": turn.timestamp,
                    "api_content": turn.api_content,
                    "input_tokens": turn.input_tokens,
                    "output_tokens": turn.output_tokens,
                    "model": turn.model,
                }
                for turn in session.turns
            ],
        }
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
