"""Live DRC execution via kicad-cli (shared by context and routing)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from utils.config import AppConfig, load_config
from utils.kicad_cli import KicadCliNotFoundError, resolve_kicad_cli


def _resolve_pcb_path(project_pro_path: Path) -> Path | None:
    pro = project_pro_path.expanduser().resolve()
    pcb = pro.parent / f"{pro.stem}.kicad_pcb"
    if pcb.is_file():
        return pcb
    alts = sorted(pro.parent.glob("*.kicad_pcb"))
    return alts[0] if alts else None


def run_live_drc(
    project_path: Path | str,
    *,
    config: AppConfig | None = None,
) -> dict[str, Any]:
    """
  Run ``kicad-cli pcb drc`` and return a normalized summary dict.

  Public API consumed by ``erc_drc_summary`` and ``inference/routing``.
  """
    cfg = config or load_config()
    pro = Path(project_path).expanduser().resolve()
    pcb_path = _resolve_pcb_path(pro)
    result: dict[str, Any] = {
        "drc_live": False,
        "drc_available": False,
        "drc_report_path": None,
        "drc_violation_count": 0,
        "drc_violation_lines": [],
        "notes": "",
    }
    if pcb_path is None:
        result["notes"] = "No .kicad_pcb file for live DRC."
        return result

    try:
        cli = resolve_kicad_cli(cfg.kicad_cli)
    except KicadCliNotFoundError as exc:
        result["notes"] = str(exc)
        return result

    report_path = pro.parent / "kicad_ai" / "exports" / f"{pro.stem}_drc.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if report_path.is_file():
        report_path.unlink()

    cmd = [
        str(cli),
        "pcb",
        "drc",
        "--format",
        "json",
        "--output",
        str(report_path),
        str(pcb_path),
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=max(30, cfg.provider_timeout_sec),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        result["notes"] = f"Live DRC failed: {exc}"
        return result

    if proc.returncode != 0 and not report_path.is_file():
        result["notes"] = (
            proc.stderr.strip()
            or proc.stdout.strip()
            or f"kicad-cli pcb drc exited {proc.returncode}"
        )
        return result

    parsed = _load_drc_report(report_path)
    violations = _extract_violation_lines(parsed)
    result.update(
        {
            "drc_live": True,
            "drc_available": True,
            "drc_report_path": str(report_path),
            "drc_violation_count": len(violations),
            "drc_violation_lines": violations[:30],
            "drc_raw": parsed,
            "notes": "Live DRC via kicad-cli.",
        }
    )
    return result


def _load_drc_report(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data


def _extract_violation_lines(parsed: dict[str, Any] | list[Any] | None) -> list[str]:
    if parsed is None:
        return []

    lines: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            desc = node.get("description") or node.get("message") or node.get("msg")
            severity = node.get("severity") or node.get("type")
            if isinstance(desc, str) and desc.strip():
                prefix = f"[{severity}] " if severity else ""
                lines.append(f"{prefix}{desc.strip()}")
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(parsed)
    if lines:
        return lines

    if isinstance(parsed, dict):
        for key in ("violations", "items", "reports", "unconnected_items"):
            block = parsed.get(key)
            if isinstance(block, list):
                for item in block:
                    if isinstance(item, str):
                        lines.append(item)
                    elif isinstance(item, dict):
                        text = item.get("description") or item.get("message")
                        if text:
                            lines.append(str(text))
    return lines
