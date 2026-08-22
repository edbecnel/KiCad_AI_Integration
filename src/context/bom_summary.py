"""BOM summary from schematic symbols (stretch slice)."""

from __future__ import annotations

from typing import Any

from context.schematic_parse import SymbolInstance


def build_bom_summary(symbols: list[SymbolInstance]) -> list[dict[str, Any]]:
    """Aggregate symbols into a BOM-style table for AI context."""
    rows: list[dict[str, Any]] = []
    for sym in symbols:
        if not sym.reference or sym.reference.startswith("#"):
            continue
        rows.append(
            {
                "reference": sym.reference,
                "value": sym.value,
                "footprint": sym.footprint,
                "lib_id": sym.lib_id,
                "datasheet": sym.datasheet,
                "sheet": sym.sheet_name,
                "custom_fields": dict(sym.custom_fields) if sym.custom_fields else {},
            }
        )
    return sorted(rows, key=lambda r: r["reference"])
