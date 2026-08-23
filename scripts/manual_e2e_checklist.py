#!/usr/bin/env python3
"""Print manual E2E checklist status and optional environment checks."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "docs/Developer_Handbook/Manual_Validation_Checklist.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual E2E validation helper")
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Check Freerouting/ngspice/kicad-cli availability",
    )
    args = parser.parse_args()

    print(f"Manual validation checklist: {CHECKLIST.relative_to(ROOT)}")
    print()
    print("Phase 1 KiCad chat E2E: run inside KiCad with Assistant shell (see checklist).")
    print("Freerouting E2E: Routing tab Ctrl+7 with open board + FREEROUTING_JAR.")
    print()

    if not args.check_env:
        return 0

    checks = {
        "FREEROUTING_JAR": os.environ.get("FREEROUTING_JAR"),
        "FREEROUTING_CLI": os.environ.get("FREEROUTING_CLI"),
        "kicad-cli": shutil.which("kicad-cli"),
        "ngspice": shutil.which("ngspice"),
    }
    for name, value in checks.items():
        status = value if value else "(not set)"
        print(f"  {name}: {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
