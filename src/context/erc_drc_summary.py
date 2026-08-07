"""ERC/DRC report discovery (file-based; KiCad API run deferred)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def collect_erc_drc_summary(project_pro_path: Path) -> dict[str, Any]:
    """
    Return ERC/DRC summary if report files exist beside the project.

    KiCad does not always emit standalone ERC/DRC text files; this scans common
    names and returns parse status for AI context.
    """
    pro = project_pro_path.expanduser().resolve()
    root = pro.parent
    result: dict[str, Any] = {
        "erc_available": False,
        "drc_available": False,
        "erc_report_path": None,
        "drc_report_path": None,
        "notes": "Run ERC/DRC in KiCad and export reports for full context.",
    }

    erc_candidates = [
        root / f"{pro.stem}-erc.rpt",
        root / "erc.rpt",
        root / "reports" / "erc.rpt",
    ]
    drc_candidates = [
        root / f"{pro.stem}-drc.rpt",
        root / "drc.rpt",
        root / "reports" / "drc.rpt",
    ]

    for path in erc_candidates:
        if path.is_file():
            result["erc_available"] = True
            result["erc_report_path"] = str(path)
            text = path.read_text(encoding="utf-8", errors="replace")
            result["erc_violation_lines"] = [
                line.strip()
                for line in text.splitlines()
                if line.strip() and "error" in line.lower()
            ][:30]
            break

    for path in drc_candidates:
        if path.is_file():
            result["drc_available"] = True
            result["drc_report_path"] = str(path)
            text = path.read_text(encoding="utf-8", errors="replace")
            result["drc_violation_lines"] = [
                line.strip()
                for line in text.splitlines()
                if line.strip() and "error" in line.lower()
            ][:30]
            break

    return result
