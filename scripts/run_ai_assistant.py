#!/usr/bin/env python3
"""
KiCad AI Assistant entry point (stretch slice).

Run from KiCad Scripting Console (Tools > Scripting Console):

    exec(open("/path/to/KiCad_AI_Integration/scripts/run_ai_assistant.py").read())

Or with an explicit project path:

    exec(open(".../run_ai_assistant.py").read()); main("/path/to/project.kicad_pro")

Datasheet HTTPS fetch policy (config key ``datasheet_url_fetch``):

- ``if_missing`` (default) — fetch only when PDF is not already in catalog/manifest
- ``always`` — re-download from URL even when a cached PDF exists (does **not** retry URLs logged as failed; full force refresh is a future UI action)
- ``never`` — no network fetches (``--no-fetch``)

Config ``url_fetch_timeout_sec`` (default 10) controls how long to wait for the server
to respond; ``url_fetch_read_timeout_sec`` (default 60) limits PDF download time after that.

``--retry-failed`` re-attempts HTTPS URLs that were previously logged as failed (after fetch improvements).

Some distributor URLs (Mouser, Littelfuse/Akamai) block automated clients even when they
work in a browser — use direct manufacturer PDF links in symbol ``Datasheet`` fields when possible.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on path when run from KiCad or repo scripts/
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from context.collector import collect_stretch_context  # noqa: E402
from context.datasheet_requirements import format_required_datasheet_notice  # noqa: E402
from utils.config import DatasheetUrlFetchPolicy, load_config  # noqa: E402


def _default_project_path() -> Path | None:
    try:
        import pcbnew  # type: ignore[import-untyped]

        board = pcbnew.GetBoard()
        if board is None:
            return None
        filename = board.GetFileName()
        if not filename:
            return None
        pcb_path = Path(filename)
        for pro in pcb_path.parent.glob("*.kicad_pro"):
            return pro
    except ImportError:
        pass
    return None


def _parse_cli_args(
    argv: list[str],
) -> tuple[str | None, bool, DatasheetUrlFetchPolicy | None, bool, bool]:
    """Return (project_path, include_image, url_fetch override, quiet, retry_failed)."""
    project_path: str | None = None
    include_image = False
    url_fetch: DatasheetUrlFetchPolicy | None = None
    quiet = False
    retry_failed = False
    for arg in argv:
        if arg == "--image":
            include_image = True
        elif arg == "--no-fetch":
            url_fetch = "never"
        elif arg == "--fetch-always":
            url_fetch = "always"
        elif arg == "--fetch-if-missing":
            url_fetch = "if_missing"
        elif arg == "--retry-failed":
            retry_failed = True
        elif arg == "--quiet":
            quiet = True
        elif not arg.startswith("-"):
            project_path = arg
    return project_path, include_image, url_fetch, quiet, retry_failed


def main(
    project_path: str | Path | None = None,
    *,
    include_image: bool = False,
    datasheet_url_fetch: DatasheetUrlFetchPolicy | None = None,
    retry_failed_urls: bool = False,
    verbose: bool = True,
) -> None:
    path = Path(project_path) if project_path else _default_project_path()
    if path is None:
        print(
            "KiCad AI Assistant: no project path. "
            "Open a board or pass main('/path/to/project.kicad_pro')."
        )
        return

    ctx = collect_stretch_context(
        path,
        include_image=include_image,
        datasheet_url_fetch=datasheet_url_fetch,
        retry_failed_urls=retry_failed_urls,
        verbose=verbose,
    )
    print(ctx.to_json(include_image_bytes=False))
    print(
        f"\n--- Summary: {len(ctx.symbols)} symbols, "
        f"{sum(1 for r in ctx.datasheet_resolutions.values() if r.status == 'resolved')} "
        f"datasheets resolved, "
        f"{sum(1 for r in ctx.datasheet_resolutions.values() if r.needs_ai_datasheet_discovery)} "
        f"need AI datasheet discovery ---"
    )
    cfg = load_config()
    notice = format_required_datasheet_notice(
        ctx.symbols,
        ctx.datasheet_resolutions,
        library_path=cfg.artifact_library_path,
    )
    if notice:
        print(f"\n{notice}")


if __name__ == "__main__":
    arg_path, include, url_fetch, quiet, retry_failed = _parse_cli_args(sys.argv[1:])
    main(
        arg_path,
        include_image=include,
        datasheet_url_fetch=url_fetch,
        retry_failed_urls=retry_failed,
        verbose=not quiet,
    )
