"""Chat session model for multi-turn conversations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ChatTurn:
    """One user or assistant turn in a session."""

    role: ChatRole
    text: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    api_content: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None

    def api_text(self) -> str:
        """Content sent to or received from the provider."""
        return self.api_content if self.api_content is not None else self.text


@dataclass
class ChatSession:
    """Ordered multi-turn history for one project."""

    project_path: Path
    turns: list[ChatTurn] = field(default_factory=list)

    def append_user(self, text: str, *, api_content: str | None = None) -> None:
        self.turns.append(
            ChatTurn(role=ChatRole.USER, text=text, api_content=api_content),
        )

    def append_assistant(
        self,
        text: str,
        *,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> None:
        self.turns.append(
            ChatTurn(
                role=ChatRole.ASSISTANT,
                text=text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            ),
        )

    def clear(self) -> None:
        self.turns.clear()

    @property
    def user_turn_count(self) -> int:
        return sum(1 for turn in self.turns if turn.role is ChatRole.USER)

    def to_api_messages(self) -> list[dict[str, Any]]:
        return [
            {"role": turn.role.value, "content": turn.api_text()}
            for turn in self.turns
        ]

    def format_conversation_log(self) -> str:
        if not self.turns:
            return ""
        lines: list[str] = []
        for turn in self.turns:
            label = "You" if turn.role is ChatRole.USER else "Assistant"
            lines.append(f"--- {label} ---\n{turn.text}\n")
        return "\n".join(lines).rstrip()
