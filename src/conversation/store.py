"""In-memory chat session store keyed by project path."""

from __future__ import annotations

from pathlib import Path

from conversation.session import ChatSession


class SessionStore:
    """Holds one ``ChatSession`` per resolved project path."""

    def __init__(self) -> None:
        self._sessions: dict[str, ChatSession] = {}

    @staticmethod
    def _key(project_path: Path | str) -> str:
        return str(Path(project_path).expanduser().resolve())

    def get_or_create(self, project_path: Path | str) -> ChatSession:
        key = self._key(project_path)
        if key not in self._sessions:
            self._sessions[key] = ChatSession(project_path=Path(key))
        return self._sessions[key]

    def reset(self, project_path: Path | str) -> ChatSession:
        key = self._key(project_path)
        session = ChatSession(project_path=Path(key))
        self._sessions[key] = session
        return session

    def get(self, project_path: Path | str) -> ChatSession | None:
        return self._sessions.get(self._key(project_path))
