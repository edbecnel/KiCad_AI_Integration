"""Persistent log of AI datasheet discovery attempts (shared library)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

AiDiscoveryOutcome = Literal[
    "downloaded",
    "fetch_failed",
    "no_url_found",
    "user_rejected",
]

DISCOVERY_LOG_VERSION = 1


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class AiDiscoveryEntry:
    part: str
    attempted_at: str
    symbol_datasheet_url: str | None = None
    suggested_urls: list[str] = field(default_factory=list)
    selected_url: str | None = None
    outcome: AiDiscoveryOutcome = "no_url_found"
    error: str | None = None
    artifact_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "part": self.part,
            "attempted_at": self.attempted_at,
            "suggested_urls": list(self.suggested_urls),
            "outcome": self.outcome,
        }
        if self.symbol_datasheet_url is not None:
            data["symbol_datasheet_url"] = self.symbol_datasheet_url
        if self.selected_url is not None:
            data["selected_url"] = self.selected_url
        if self.error is not None:
            data["error"] = self.error
        if self.artifact_id is not None:
            data["artifact_id"] = self.artifact_id
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AiDiscoveryEntry:
        return cls(
            part=data["part"],
            attempted_at=data.get("attempted_at", ""),
            symbol_datasheet_url=data.get("symbol_datasheet_url"),
            suggested_urls=list(data.get("suggested_urls") or []),
            selected_url=data.get("selected_url"),
            outcome=data.get("outcome", "no_url_found"),
            error=data.get("error"),
            artifact_id=data.get("artifact_id"),
        )


class AiDiscoveryLog:
    """Records per-part AI discovery attempts for audit and UI messaging."""

    def __init__(self, library_path: Path) -> None:
        self.library_path = library_path.expanduser().resolve()
        self.log_path = self.library_path / "ai_discovery_log.json"
        self._entries: list[AiDiscoveryEntry] | None = None
        self._dirty = False

    def bootstrap(self) -> None:
        self.library_path.mkdir(parents=True, exist_ok=True)
        if not self.log_path.is_file():
            self._write({"version": DISCOVERY_LOG_VERSION, "entries": []})

    def load(self) -> list[AiDiscoveryEntry]:
        if self._entries is None:
            self.bootstrap()
            with self.log_path.open(encoding="utf-8") as fh:
                data = json.load(fh)
            self._entries = [
                AiDiscoveryEntry.from_dict(raw) for raw in data.get("entries", [])
            ]
        return self._entries

    @property
    def entries(self) -> list[AiDiscoveryEntry]:
        return self.load()

    def get_latest(self, part: str) -> AiDiscoveryEntry | None:
        part_norm = part.strip()
        for entry in reversed(self.entries):
            if entry.part == part_norm:
                return entry
        return None

    def record_attempt(
        self,
        part: str,
        *,
        symbol_datasheet_url: str | None = None,
        suggested_urls: list[str] | None = None,
        selected_url: str | None = None,
        outcome: AiDiscoveryOutcome,
        error: str | None = None,
        artifact_id: str | None = None,
    ) -> AiDiscoveryEntry:
        part_norm = part.strip()
        now = _utc_now()
        entry = AiDiscoveryEntry(
            part=part_norm,
            attempted_at=now,
            symbol_datasheet_url=symbol_datasheet_url,
            suggested_urls=list(suggested_urls or []),
            selected_url=selected_url,
            outcome=outcome,
            error=error,
            artifact_id=artifact_id,
        )
        self.entries.append(entry)
        self._dirty = True
        return entry

    def save(self) -> None:
        if not self._dirty or self._entries is None:
            return
        self._write(
            {
                "version": DISCOVERY_LOG_VERSION,
                "entries": [entry.to_dict() for entry in self._entries],
            }
        )
        self._dirty = False

    def _write(self, data: dict[str, Any]) -> None:
        self.library_path.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        self._entries = [
            AiDiscoveryEntry.from_dict(raw) for raw in data.get("entries", [])
        ]
