#!/usr/bin/env python3
"""Export user-library circuit families to a CKES/ELS migration bundle."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reasoning.family_registry import DEFAULT_LEARNING_LIBRARY_SUBDIR, load_families
from utils.config import load_config


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def export_bundle(output_dir: Path, *, library_path: Path | None = None) -> Path:
    cfg = load_config()
    lib_root = Path(library_path or cfg.artifact_library_path).expanduser()
    families_root = lib_root / cfg.learning_library_subdir
    if not families_root.is_dir():
        raise SystemExit(f"No circuit families directory: {families_root}")

    families = load_families(library_path=lib_root, config=cfg)
    learned = [f for f in families if f.families_root == families_root]
    if not learned:
        raise SystemExit(f"No learned families in {families_root}")

    stamp = _utc_stamp()
    bundle_dir = output_dir.expanduser().resolve() / f"ckes_circuit_families_{stamp}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    manifest_src = families_root / "families.json"
    shutil.copy2(manifest_src, bundle_dir / "families.json")

    for family in learned:
        src_dir = families_root / family.directory
        if src_dir.is_dir():
            shutil.copytree(src_dir, bundle_dir / family.directory)

    meta = {
        "export_format": "ckes_circuit_families_v1",
        "exported_at": stamp,
        "source_library": str(lib_root),
        "family_count": len(learned),
        "family_ids": [f.family_id for f in learned],
    }
    (bundle_dir / "export_metadata.json").write_text(
        json.dumps(meta, indent=2) + "\n",
        encoding="utf-8",
    )
    return bundle_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Export library circuit families for CKES/ELS")
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=str(Path.home() / "kicad_ai_exports"),
        help="Directory to write export bundle",
    )
    parser.add_argument(
        "--library",
        dest="library_path",
        help="Artifact library path (default: from config)",
    )
    args = parser.parse_args()
    bundle = export_bundle(
        Path(args.output_dir),
        library_path=Path(args.library_path).expanduser() if args.library_path else None,
    )
    print(f"Exported CKES bundle: {bundle}")


if __name__ == "__main__":
    main()
