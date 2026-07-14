"""Compact ProjectContext for large prompts."""

from __future__ import annotations

from typing import Any

from context.model import ProjectContext

_SYMBOL_FULL_LIMIT = 50


def compact_context_for_prompt(ctx: ProjectContext) -> dict[str, Any]:
    """
    Shrink context JSON for large schematics to reduce tokens and upload time.

    Full symbol list is kept when <= ``_SYMBOL_FULL_LIMIT``; otherwise a compact
    table plus unresolved datasheet entries only.
    """
    data = ctx.to_dict(include_image_bytes=False)
    symbols = data.get("symbols") or []
    if len(symbols) <= _SYMBOL_FULL_LIMIT:
        return data

    data["symbol_count"] = len(symbols)
    data["symbols"] = [
        {
            "reference": s.get("reference"),
            "value": s.get("value"),
            "footprint": s.get("footprint"),
            "lib_id": s.get("lib_id"),
        }
        for s in symbols
    ]
    resolutions: dict[str, Any] = data.pop("datasheet_resolutions", {}) or {}
    unresolved = {
        ref: res
        for ref, res in resolutions.items()
        if res.get("status") in ("missing", "fetch_failed")
    }
    data["datasheet_resolutions_unresolved"] = unresolved
    data["datasheet_summary"] = {
        "resolved": sum(1 for r in resolutions.values() if r.get("status") == "resolved"),
        "missing_or_failed": len(unresolved),
        "total_references": len(resolutions),
    }
    data["_note"] = (
        f"Large schematic ({len(symbols)} symbols): compact symbol table sent; "
        "full pin/datasheet detail omitted to limit request size."
    )
    return data
