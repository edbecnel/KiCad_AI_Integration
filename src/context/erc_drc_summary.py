"""ERC/DRC report discovery with optional live DRC via kicad-cli."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from utils.config import AppConfig, load_config


def collect_erc_drc_summary(
    project_pro_path: Path,
    *,
    config: AppConfig | None = None,
) -> dict[str, Any]:
    """
    Return ERC/DRC summary from live DRC when available, else saved report files.

    Live DRC uses ``context.live.drc_runner.run_live_drc`` (shared with routing).
    """
    pro = project_pro_path.expanduser().resolve()
    result: dict[str, Any] = {
        "erc_available": False,
        "drc_available": False,
        "erc_report_path": None,
        "drc_report_path": None,
        "drc_live": False,
        "notes": "Run ERC/DRC in KiCad and export reports for full context.",
    }

    from context.live.drc_runner import run_live_drc

    live_drc = run_live_drc(pro, config=config or load_config())
    if live_drc.get("drc_available"):
        result.update(live_drc)
        result["drc_available"] = True
        if live_drc.get("drc_violation_count", 0) == 0:
            result["status_line"] = "DRC: no violations (live kicad-cli run)"
        else:
            result["status_line"] = (
                f"DRC: {live_drc.get('drc_violation_count', 0)} violations (live)"
            )

    erc_candidates = [
        pro.parent / f"{pro.stem}-erc.rpt",
        pro.parent / "erc.rpt",
        pro.parent / "reports" / "erc.rpt",
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

    if not result.get("drc_available"):
        drc_candidates = [
            pro.parent / f"{pro.stem}-drc.rpt",
            pro.parent / "drc.rpt",
            pro.parent / "reports" / "drc.rpt",
        ]
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
                result["status_line"] = (
                    f"DRC: {len(result['drc_violation_lines'])} error lines (report file)"
                )
                break

    return result
