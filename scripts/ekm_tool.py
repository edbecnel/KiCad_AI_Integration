#!/usr/bin/env python3
"""Headless EKM inspect/validate CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ekm import (  # noqa: E402
    EKMError,
    document_summary,
    init_empty,
    load,
    resolve_ekm_path,
    validate_document_data,
)
from ekm.io import load_json_file  # noqa: E402


def cmd_validate(path: Path) -> int:
    ekm_path = resolve_ekm_path(path)
    validate_document_data(load_json_file(ekm_path))
    print(f"OK: {ekm_path}")
    return 0


def cmd_init(project_dir: Path, *, project_path: str | None) -> int:
    out = init_empty(project_dir, project_path=project_path)
    print(f"Created: {out}")
    return 0


def cmd_show(path: Path) -> int:
    doc = load(path)
    print(json.dumps(document_summary(doc), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EKM engineering knowledge tools")
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="Validate engineering_knowledge.json")
    p_val.add_argument("path", help="EKM file or project directory")

    p_init = sub.add_parser("init", help="Create empty EKM in project kicad_ai/")
    p_init.add_argument("project_dir", help="Project root directory")
    p_init.add_argument(
        "--project-path",
        help="Optional .kicad_pro path stored in the document",
    )

    p_show = sub.add_parser("show", help="Print document summary JSON")
    p_show.add_argument("path", help="EKM file or project directory")

    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            return cmd_validate(Path(args.path))
        if args.command == "init":
            return cmd_init(Path(args.project_dir), project_path=args.project_path)
        if args.command == "show":
            return cmd_show(Path(args.path))
    except EKMError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
