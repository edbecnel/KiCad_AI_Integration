"""Persistent log of HTTPS datasheet URL fetch outcomes (shared library)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

UrlFetchStatus = Literal["downloaded", "failed"]
FETCH_LOG_VERSION = 1


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class UrlFetchEntry:
    part: str
    source_url: str
    status: UrlFetchStatus
    artifact_id: str | None = None
    error: str | None = None
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "part": self.part,
            "source_url": self.source_url,
            "status": self.status,
            "updated_at": self.updated_at,
        }
        if self.artifact_id is not None:
            data["artifact_id"] = self.artifact_id
        if self.error is not None:
            data["error"] = self.error
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UrlFetchEntry:
        return cls(
            part=data["part"],
            source_url=data["source_url"],
            status=data["status"],
            artifact_id=data.get("artifact_id"),
            error=data.get("error"),
            updated_at=data.get("updated_at", ""),
        )


class UrlFetchLog:
    """Records per-part HTTPS URL outcomes so fetches are not repeated."""

    def __init__(self, library_path: Path) -> None:
        self.library_path = library_path.expanduser().resolve()
        self.log_path = self.library_path / "url_fetch_log.json"
        self._entries: list[UrlFetchEntry] | None = None
        self._dirty = False

    def bootstrap(self) -> None:
        self.library_path.mkdir(parents=True, exist_ok=True)
        if not self.log_path.is_file():
            self._write({"version": FETCH_LOG_VERSION, "entries": []})

    def load(self) -> list[UrlFetchEntry]:
        if self._entries is None:
            self.bootstrap()
            with self.log_path.open(encoding="utf-8") as fh:
                data = json.load(fh)
            self._entries = [
                UrlFetchEntry.from_dict(raw) for raw in data.get("entries", [])
            ]
        return self._entries

    @property
    def entries(self) -> list[UrlFetchEntry]:
        return self.load()

    def failed_urls(self) -> set[str]:
        return {entry.source_url for entry in self.entries if entry.status == "failed"}

    def get(self, part: str, source_url: str) -> UrlFetchEntry | None:
        part_norm = part.strip()
        for entry in reversed(self.entries):
            if entry.part == part_norm and entry.source_url == source_url:
                return entry
        return None

    def record_downloaded(
        self,
        part: str,
        source_url: str,
        *,
        artifact_id: str,
    ) -> UrlFetchEntry:
        return self._upsert(
            part,
            source_url,
            status="downloaded",
            artifact_id=artifact_id,
            error=None,
        )

    def record_failed(
        self,
        part: str,
        source_url: str,
        *,
        error: str,
    ) -> UrlFetchEntry:
        return self._upsert(
            part,
            source_url,
            status="failed",
            artifact_id=None,
            error=error,
        )

    def _upsert(
        self,
        part: str,
        source_url: str,
        *,
        status: UrlFetchStatus,
        artifact_id: str | None,
        error: str | None,
    ) -> UrlFetchEntry:
        part_norm = part.strip()
        now = _utc_now()
        for entry in self.entries:
            if entry.part == part_norm and entry.source_url == source_url:
                entry.status = status
                entry.artifact_id = artifact_id
                entry.error = error
                entry.updated_at = now
                self._dirty = True
                return entry
        entry = UrlFetchEntry(
            part=part_norm,
            source_url=source_url,
            status=status,
            artifact_id=artifact_id,
            error=error,
            updated_at=now,
        )
        self.entries.append(entry)
        self._dirty = True
        return entry

    def save(self) -> None:
        if not self._dirty or self._entries is None:
            return
        self._write(
            {
                "version": FETCH_LOG_VERSION,
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
            UrlFetchEntry.from_dict(raw) for raw in data.get("entries", [])
        ]
