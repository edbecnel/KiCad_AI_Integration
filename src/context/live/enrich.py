"""Enrich ProjectContext with live KiCad data when available."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from context.live.board_settings import collect_live_board_settings
from context.live.editor_context import collect_editor_context
from context.live.firmware import load_firmware_summary
from context.live.probe import get_live_board, is_pcbnew_available
from context.live.selection import collect_selection_context
from context.model import ProjectContext
from utils.config import AppConfig


def enrich_live_context(
    ctx: ProjectContext,
    project_path: Path | str,
    *,
    config: AppConfig | None = None,
    use_selection: bool = False,
    firmware_path: Path | str | None = None,
) -> ProjectContext:
    """Attach live editor/board data to an existing ProjectContext."""
    pro = Path(project_path).expanduser().resolve()
    live: dict[str, Any] = {}
    sources: list[str] = []

    editor = collect_editor_context()
    if editor.get("available"):
        live["editor"] = editor
        sources.append("pcbnew")

    board_settings = collect_live_board_settings(pro)
    if board_settings.get("available"):
        live["board_settings"] = board_settings
        if board_settings.get("source") == "pcbnew":
            sources.append("pcbnew")
        elif board_settings.get("source") == "file":
            sources.append("file")

    if is_pcbnew_available() and get_live_board() is not None:
        live["pcbnew_embedded"] = True

    if use_selection:
        selection = collect_selection_context()
        ctx.selection_context = selection
        if selection.get("available"):
            live["selection"] = selection

    if firmware_path:
        fw = load_firmware_summary(firmware_path)
        ctx.firmware_summary = fw
        if fw and fw.get("available"):
            live["firmware"] = {"path": fw.get("path"), "byte_size": fw.get("byte_size")}

    if live:
        ctx.live_context = live
        ctx.live_source = "+".join(dict.fromkeys(sources)) if sources else None
    else:
        ctx.live_context = None
        ctx.live_source = None
    return ctx
