"""Static context snapshot cache for multi-turn chat follow-ups."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from context.fingerprint import ProjectFingerprint, compute_fingerprint, save_fingerprint
from context.model import ProjectContext

CACHE_FILENAME = "context_cache.json"


def context_cache_file_path(project_path: Path | str) -> Path:
    """Return ``<project_root>/kicad_ai/context_cache.json``."""
    pro = Path(project_path).expanduser().resolve()
    return pro.parent / "kicad_ai" / CACHE_FILENAME


@dataclass
class ContextSnapshot:
    """Lightweight static context for follow-up prompts (no image bytes)."""

    project_name: str
    symbol_count: int
    netlist_status_line: str | None = None
    pcb_summary_line: str | None = None
    bom_line_count: int = 0
    erc_drc_line: str | None = None
    schematic_files: list[str] = field(default_factory=list)
    datasheet_resolved_count: int = 0
    prompt_context_excerpt: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "symbol_count": self.symbol_count,
            "netlist_status_line": self.netlist_status_line,
            "pcb_summary_line": self.pcb_summary_line,
            "bom_line_count": self.bom_line_count,
            "erc_drc_line": self.erc_drc_line,
            "schematic_files": list(self.schematic_files),
            "datasheet_resolved_count": self.datasheet_resolved_count,
            "prompt_context_excerpt": self.prompt_context_excerpt,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextSnapshot:
        schematics = data.get("schematic_files")
        return cls(
            project_name=str(data.get("project_name", "")),
            symbol_count=int(data.get("symbol_count", 0)),
            netlist_status_line=data.get("netlist_status_line"),
            pcb_summary_line=data.get("pcb_summary_line"),
            bom_line_count=int(data.get("bom_line_count", 0)),
            erc_drc_line=data.get("erc_drc_line"),
            schematic_files=[str(s) for s in schematics] if isinstance(schematics, list) else [],
            datasheet_resolved_count=int(data.get("datasheet_resolved_count", 0)),
            prompt_context_excerpt=data.get("prompt_context_excerpt"),
        )

    def format_summary(self) -> str:
        parts = [
            f"Project: {self.project_name}",
            f"Symbols: {self.symbol_count}",
        ]
        if self.netlist_status_line:
            parts.append(self.netlist_status_line)
        if self.pcb_summary_line:
            parts.append(self.pcb_summary_line)
        if self.erc_drc_line:
            parts.append(self.erc_drc_line)
        if self.bom_line_count:
            parts.append(f"BOM lines: {self.bom_line_count}")
        if self.datasheet_resolved_count:
            parts.append(f"Datasheets resolved: {self.datasheet_resolved_count}")
        return "; ".join(parts)


@dataclass
class ContextCacheEntry:
    fingerprint: ProjectFingerprint
    snapshot: ContextSnapshot

    def to_dict(self) -> dict[str, Any]:
        return {
            "fingerprint": self.fingerprint.to_dict(),
            "snapshot": self.snapshot.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextCacheEntry:
        fp_raw = data.get("fingerprint")
        snap_raw = data.get("snapshot")
        if not isinstance(fp_raw, dict) or not isinstance(snap_raw, dict):
            raise ValueError("Invalid context cache entry")
        return cls(
            fingerprint=ProjectFingerprint.from_dict(fp_raw),
            snapshot=ContextSnapshot.from_dict(snap_raw),
        )


def snapshot_from_context(ctx: ProjectContext, *, prompt_excerpt: str | None = None) -> ContextSnapshot:
    """Build a cacheable snapshot from a collected ``ProjectContext``."""
    netlist_line = None
    if ctx.netlist_summary:
        netlist_line = ctx.netlist_summary.get("status_line")
        if netlist_line is not None:
            netlist_line = str(netlist_line)

    pcb_line = None
    if ctx.pcb_summary:
        pcb_line = ctx.pcb_summary.get("status_line") or ctx.pcb_summary.get("summary")
        if pcb_line is not None:
            pcb_line = str(pcb_line)

    erc_line = None
    if ctx.erc_drc_summary:
        erc_line = ctx.erc_drc_summary.get("status_line") or ctx.erc_drc_summary.get("summary")
        if erc_line is not None:
            erc_line = str(erc_line)

    resolved = sum(
        1 for res in ctx.datasheet_resolutions.values() if res.status == "resolved"
    )

    return ContextSnapshot(
        project_name=ctx.project_name,
        symbol_count=len(ctx.symbols),
        netlist_status_line=netlist_line,
        pcb_summary_line=pcb_line,
        bom_line_count=len(ctx.bom_summary or []),
        erc_drc_line=erc_line,
        schematic_files=list(ctx.schematics),
        datasheet_resolved_count=resolved,
        prompt_context_excerpt=prompt_excerpt,
    )


def load_context_cache(project_path: Path | str) -> ContextCacheEntry | None:
    path = context_cache_file_path(project_path)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    try:
        return ContextCacheEntry.from_dict(data)
    except ValueError:
        return None


def save_context_cache(
    project_path: Path | str,
    ctx: ProjectContext,
    *,
    prompt_excerpt: str | None = None,
) -> ContextCacheEntry:
    """Persist snapshot and fingerprint after a successful context collection."""
    fingerprint = compute_fingerprint(project_path)
    entry = ContextCacheEntry(
        fingerprint=fingerprint,
        snapshot=snapshot_from_context(ctx, prompt_excerpt=prompt_excerpt),
    )
    path = context_cache_file_path(project_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entry.to_dict(), indent=2) + "\n", encoding="utf-8")
    save_fingerprint(fingerprint)
    return entry


def cache_matches_project(project_path: Path | str) -> bool:
    """Return True when on-disk cache fingerprint matches the current project files."""
    cached = load_context_cache(project_path)
    if cached is None:
        return False
    current = compute_fingerprint(project_path)
    return cached.fingerprint.layers == current.layers
