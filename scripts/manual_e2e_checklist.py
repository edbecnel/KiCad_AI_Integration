#!/usr/bin/env python3
"""Print manual E2E checklist status and optional environment checks."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
CHECKLIST = ROOT / "docs/Developer_Handbook/Manual_Validation_Checklist.md"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def collect_shell_env_checks() -> dict[str, str | None]:
    """Environment variables and PATH lookups visible to this shell."""
    return {
        "FREEROUTING_JAR": os.environ.get("FREEROUTING_JAR"),
        "FREEROUTING_CLI": os.environ.get("FREEROUTING_CLI"),
        "kicad-cli (PATH)": shutil.which("kicad-cli"),
        "ngspice (PATH)": shutil.which("ngspice"),
    }


def collect_config_checks() -> dict[str, str]:
    """Settings from ~/kicad_ai_config.json and KAI resolution logic."""
    from utils.config import default_config_path, load_config
    from utils.freerouting_cli import try_resolve_freerouting

    env_override = os.environ.get("KICAD_AI_CONFIG")
    config_path = (
        Path(env_override).expanduser()
        if env_override
        else default_config_path()
    )
    cfg = load_config()

    checks: dict[str, str] = {
        "config_file": str(config_path) if config_path.is_file() else f"{config_path} (missing)",
        "routing_enabled": str(cfg.routing_enabled).lower(),
        "freerouting_jar (config)": cfg.freerouting_jar or "(not set)",
        "freerouting_cli (config)": cfg.freerouting_cli or "(not set)",
        "kicad_cli (config)": cfg.kicad_cli or "(not set)",
        "anthropic_api_key (config)": (
            "(set)" if (cfg.anthropic_api_key or "").strip() else "(not set)"
        ),
    }

    resolution = try_resolve_freerouting(
        jar=cfg.freerouting_jar,
        cli=cfg.freerouting_cli,
    )
    if resolution is not None and resolution.installed:
        if resolution.jar_path is not None:
            checks["freerouting (resolved)"] = str(resolution.jar_path)
        elif resolution.cli_path is not None:
            checks["freerouting (resolved)"] = str(resolution.cli_path)
    else:
        checks["freerouting (resolved)"] = "(not found)"

    effective_cli = cfg.kicad_cli or shutil.which("kicad-cli")
    checks["kicad-cli (effective)"] = effective_cli or "(not set)"

    return checks


def _format_checks(checks: dict[str, Any]) -> str:
    lines = []
    for name, value in checks.items():
        status = value if value else "(not set)"
        lines.append(f"  {name}: {status}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual E2E validation helper")
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Check shell env vars and ~/kicad_ai_config.json paths",
    )
    args = parser.parse_args()

    print(f"Manual validation checklist: {CHECKLIST.relative_to(ROOT)}")
    print()
    print("Phase 1 KiCad chat E2E: run inside KiCad with Assistant shell (see checklist).")
    print("Freerouting E2E: Routing tab Ctrl+7 — config file and/or FREEROUTING_* env.")
    print("Sign-off: check boxes in Manual_Validation_Checklist.md — human-only, not automated.")
    print()

    if not args.check_env:
        return 0

    print("Shell environment (this terminal only):")
    print(_format_checks(collect_shell_env_checks()))
    print()
    print("KiCad AI config (used by the plugin):")
    print(_format_checks(collect_config_checks()))
    print()
    print(
        "Note: KiCad launched from the Dock may not inherit shell env vars. "
        "Prefer ~/kicad_ai_config.json for Freerouting and API keys."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
