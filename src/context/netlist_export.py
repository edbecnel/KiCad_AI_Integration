"""Netlist export summary (kicad-cli when available)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from utils.config import AppConfig, load_config


def collect_netlist_summary(
    project_pro_path: Path,
    *,
    config: AppConfig | None = None,
) -> dict[str, Any] | None:
    """
    Export a SPICE netlist via kicad-cli when available.

    Returns None when kicad-cli is missing or export fails.
    """
    cfg = config or load_config()
    cli = cfg.kicad_cli or shutil.which("kicad-cli")
    if not cli:
        return None

    pro = project_pro_path.expanduser().resolve()
    sch = pro.parent / f"{pro.stem}.kicad_sch"
    if not sch.is_file():
        return None

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "netlist.net"
        try:
            subprocess.run(
                [
                    cli,
                    "sch",
                    "export",
                    "netlist",
                    "--format",
                    "spice",
                    "-o",
                    str(out),
                    str(sch),
                ],
                check=True,
                capture_output=True,
                timeout=60,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            return None

        if not out.is_file():
            return None
        text = out.read_text(encoding="utf-8", errors="replace")
        lines = [line for line in text.splitlines() if line.strip()]
        from context.simulation_gaps import parse_spice_netlist_includes

        includes = parse_spice_netlist_includes(text)
        return {
            "format": "spice",
            "line_count": len(lines),
            "preview_lines": lines[:40],
            "include_paths": includes,
            "text": text,
        }
