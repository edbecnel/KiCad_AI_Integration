"""Netlist export summary (kicad-cli when available)."""

from __future__ import annotations

import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from utils.config import AppConfig, load_config
from utils.kicad_cli import KicadCliNotFoundError, resolve_kicad_cli

from context.schematic_parse import discover_schematic_paths

RunSubprocess = Callable[..., subprocess.CompletedProcess[str]]


def _parse_export_warnings(stderr: str) -> list[str]:
    """Return non-empty stderr lines, omitting noisy fontconfig chatter."""
    warnings: list[str] = []
    for line in stderr.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("Fontconfig"):
            continue
        warnings.append(stripped)
    return warnings


def _is_usable_netlist(text: str) -> bool:
    """True when the export contains more than an empty KiCad SPICE shell."""
    substantive = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith(".title") and line.strip() != ".end"
    ]
    return bool(substantive)


def _build_netlist_summary(
    text: str,
    *,
    exit_code: int,
    stderr: str = "",
) -> dict[str, Any]:
    from context.simulation_gaps import parse_spice_netlist_includes

    lines = [line for line in text.splitlines() if line.strip()]
    includes = parse_spice_netlist_includes(text)
    warnings = _parse_export_warnings(stderr)
    export_status = "ok" if exit_code == 0 else "partial"
    summary: dict[str, Any] = {
        "format": "spice",
        "line_count": len(lines),
        "preview_lines": lines[:40],
        "include_paths": includes,
        "text": text,
        "export_status": export_status,
        "kicad_cli_exit_code": exit_code,
    }
    if warnings:
        summary["warnings"] = warnings
    return summary


def collect_netlist_summary(
    project_pro_path: Path,
    *,
    config: AppConfig | None = None,
    run_subprocess: RunSubprocess | None = None,
) -> dict[str, Any] | None:
    """
    Export a SPICE netlist via kicad-cli when available.

    KiCad may exit with code 2 when some symbols lack simulation models while
    still writing a usable netlist. Those partial exports are accepted.

    Returns None when kicad-cli is missing, the schematic is absent, or export
    produces no substantive netlist content.
    """
    cfg = config or load_config()
    try:
        cli = resolve_kicad_cli(cfg.kicad_cli)
    except KicadCliNotFoundError:
        return None

    pro = project_pro_path.expanduser().resolve()
    schematic_paths = discover_schematic_paths(pro)
    if not schematic_paths:
        return None
    sch = schematic_paths[0]
    if not sch.is_file():
        return None

    runner = run_subprocess or subprocess.run

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "netlist.net"
        try:
            result = runner(
                [
                    str(cli),
                    "sch",
                    "export",
                    "netlist",
                    "--format",
                    "spice",
                    "-o",
                    str(out),
                    str(sch),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except (subprocess.TimeoutExpired, OSError):
            return None

        if not out.is_file():
            return None
        text = out.read_text(encoding="utf-8", errors="replace")
        if not _is_usable_netlist(text):
            return None

        stderr = result.stderr if isinstance(result.stderr, str) else ""
        exit_code = int(result.returncode)
        return _build_netlist_summary(text, exit_code=exit_code, stderr=stderr)


def format_netlist_status_line(netlist_summary: dict[str, Any] | None) -> str:
    """Human-readable SPICE netlist status for UI context previews."""
    if not netlist_summary:
        return (
            "SPICE netlist: not exported "
            "(kicad-cli unavailable or no substantive output)"
        )
    line_count = int(netlist_summary.get("line_count") or 0)
    status = str(netlist_summary.get("export_status") or "ok")
    warnings = netlist_summary.get("warnings") or []
    if status == "partial":
        detail = "partial"
        if warnings:
            detail += f" — {warnings[0]}"
            if len(warnings) > 1:
                detail += f" (+{len(warnings) - 1} more)"
        return f"SPICE netlist: {line_count} lines ({detail})"
    return f"SPICE netlist: {line_count} lines"
