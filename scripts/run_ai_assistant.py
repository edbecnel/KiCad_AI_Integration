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

``--ui-datasheets`` opens the Missing Required Datasheets wxPython panel (requires wx; use inside KiCad or a wx-enabled Python).

``--ui-chat`` opens the KiCad AI chat panel with context preview and Approve & Send (requires wx).

``--ui-simulation`` opens the Simulation models (SUBCKT) wxPython panel.

``--ask "question"`` sends a prompt to Claude via the prompt builder (requires API key in config). Dev smoke path — bypasses Approve & Send UI.

``--reset-datasheet VALUE`` clears cached PDF links for one part Value and re-resolves.

``--ai-datasheets`` enables opt-in AI datasheet URL suggestion after HTTPS fetch failure.
``--ai-datasheets-auto-fetch`` also downloads suggested URLs without per-URL approval.

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
from prompts import build_general_review_prompt  # noqa: E402
from providers import get_provider  # noqa: E402
from providers.errors import ProviderError  # noqa: E402
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
) -> tuple[
    str | None,
    bool,
    DatasheetUrlFetchPolicy | None,
    bool,
    bool,
    bool,
    bool,
    bool,
    bool,
    bool,
    list[str],
    str | None,
]:
    """Return (project_path, include_image, url_fetch, quiet, retry_failed, ui_datasheets, ui_chat, ui_simulation, ai_datasheets, ai_datasheets_auto_fetch, reset_datasheets, ask)."""
    project_path: str | None = None
    include_image = False
    url_fetch: DatasheetUrlFetchPolicy | None = None
    quiet = False
    retry_failed = False
    ui_datasheets = False
    ui_chat = False
    ui_simulation = False
    ai_datasheets = False
    ai_datasheets_auto_fetch = False
    reset_datasheets: list[str] = []
    ask: str | None = None
    i = 0
    while i < len(argv):
        arg = argv[i]
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
        elif arg == "--ui-datasheets":
            ui_datasheets = True
        elif arg == "--ui-chat":
            ui_chat = True
        elif arg == "--ui-simulation":
            ui_simulation = True
        elif arg == "--ai-datasheets":
            ai_datasheets = True
        elif arg == "--ai-datasheets-auto-fetch":
            ai_datasheets = True
            ai_datasheets_auto_fetch = True
        elif arg == "--reset-datasheet":
            if i + 1 >= len(argv):
                raise SystemExit("--reset-datasheet requires a part Value")
            reset_datasheets.append(argv[i + 1])
            i += 1
        elif arg == "--quiet":
            quiet = True
        elif arg == "--ask":
            if i + 1 >= len(argv):
                raise SystemExit("--ask requires a question string")
            ask = argv[i + 1]
            i += 1
        elif not arg.startswith("-"):
            project_path = arg
        i += 1
    return (
        project_path,
        include_image,
        url_fetch,
        quiet,
        retry_failed,
        ui_datasheets,
        ui_chat,
        ui_simulation,
        ai_datasheets,
        ai_datasheets_auto_fetch,
        reset_datasheets,
        ask,
    )


def main(
    project_path: str | Path | None = None,
    *,
    include_image: bool = False,
    datasheet_url_fetch: DatasheetUrlFetchPolicy | None = None,
    retry_failed_urls: bool = False,
    datasheet_ai_discovery: bool = False,
    datasheet_ai_discovery_auto_fetch: bool = False,
    reset_datasheets: list[str] | None = None,
    verbose: bool = True,
) -> None:
    path = Path(project_path) if project_path else _default_project_path()
    if path is None:
        print(
            "KiCad AI Assistant: no project path. "
            "Open a board or pass main('/path/to/project.kicad_pro')."
        )
        return

    ctx = None
    if reset_datasheets:
        from ui.datasheet_supply import reset_datasheet_for_part

        for part in reset_datasheets:
            if verbose:
                print(f"Resetting datasheet for {part}…", file=sys.stderr)
            ctx = reset_datasheet_for_part(
                path,
                part,
                rerun_ai_discovery=datasheet_ai_discovery or None,
                verbose=verbose,
            )

    if ctx is None:
        ctx = collect_stretch_context(
            path,
            include_image=include_image,
            datasheet_url_fetch=datasheet_url_fetch,
            retry_failed_urls=retry_failed_urls,
            datasheet_ai_discovery=datasheet_ai_discovery or None,
            datasheet_ai_discovery_auto_fetch=datasheet_ai_discovery_auto_fetch or None,
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
        ai_discovery_results=ctx.ai_discovery_results,
    )
    if notice:
        print(f"\n{notice}")
    from context.simulation_gaps import summarize_simulation_gaps
    from context.artifacts.store import ArtifactStore

    pro = Path(path).expanduser().resolve()
    if pro.is_dir():
        pros = sorted(pro.glob("*.kicad_pro"))
        pro = pros[0] if pros else pro
    project_root = pro.parent if pro.suffix == ".kicad_pro" else pro
    sim_rows = summarize_simulation_gaps(
        ctx.symbols,
        project_root=project_root,
        resolutions=ctx.datasheet_resolutions,
        store=ArtifactStore(cfg.artifact_library_path),
        netlist_text=(
            str(ctx.netlist_summary.get("text"))
            if ctx.netlist_summary and ctx.netlist_summary.get("text")
            else None
        ),
        missing_only=True,
    )
    if sim_rows:
        print("\n--- Simulation models missing ---")
        for row in sim_rows:
            print(f"  {row.part} ({', '.join(row.references)}): {row.gap_detail}")


def main_ask(
    project_path: str | Path | None,
    question: str,
    *,
    include_image: bool = False,
    datasheet_url_fetch: DatasheetUrlFetchPolicy | None = None,
    retry_failed_urls: bool = False,
    verbose: bool = True,
) -> None:
    """
    Dev smoke path: collect context and send a built prompt to Claude.

    Bypasses the Approve & Send UI — for local development only.
    """
    path = Path(project_path) if project_path else _default_project_path()
    if path is None:
        print(
            "KiCad AI Assistant: no project path. "
            "Open a board or pass a .kicad_pro path."
        )
        return

    cfg = load_config()
    ctx = collect_stretch_context(
        path,
        config=cfg,
        include_image=include_image,
        datasheet_url_fetch=datasheet_url_fetch,
        retry_failed_urls=retry_failed_urls,
        verbose=verbose,
    )
    built = build_general_review_prompt(ctx, question, include_image=include_image)
    provider = get_provider(cfg)
    try:
        response = provider.send_message(
            built.text,
            system=built.system,
            image=ctx.schematic_image if built.include_image else None,
            config=cfg,
        )
    except ProviderError as exc:
        print(f"Provider error: {exc}")
        return

    print("--- Claude response ---")
    print(response.text)
    print(
        f"\n--- Tokens: {response.usage.input_tokens} in, "
        f"{response.usage.output_tokens} out "
        f"(model: {response.model}, template: {built.template}) ---"
    )


def main_ui_chat(
    project_path: str | Path | None = None,
    *,
    retry_failed_urls: bool = False,
    force_refresh_urls: bool = False,
) -> None:
    """Open the KiCad AI chat panel."""
    try:
        import wx  # noqa: F401
    except ImportError:
        print("Chat UI requires wxPython (run inside KiCad or install wx).")
        return

    path = Path(project_path) if project_path else _default_project_path()
    if path is None:
        print("No project path. Pass a .kicad_pro path or open a board in KiCad.")
        return

    from ui.launcher import show_chat_dialog

    show_chat_dialog(
        path,
        retry_failed_urls=retry_failed_urls,
        force_refresh_urls=force_refresh_urls,
    )


def main_ui_datasheets(
    project_path: str | Path | None = None,
    *,
    retry_failed_urls: bool = False,
    ai_datasheets: bool = False,
) -> None:
    """Open the Missing Required Datasheets panel."""
    try:
        import wx  # noqa: F401 — availability check
    except ImportError:
        print("Missing datasheets UI requires wxPython (run inside KiCad or install wx).")
        return

    path = Path(project_path) if project_path else _default_project_path()
    if path is None:
        print("No project path. Pass a .kicad_pro path or open a board in KiCad.")
        return

    from ui.launcher import show_missing_datasheets_dialog

    show_missing_datasheets_dialog(path, retry_failed_urls=retry_failed_urls, ai_datasheets=ai_datasheets)


def main_ui_simulation(project_path: str | Path | None = None) -> None:
    """Open the Simulation models (SUBCKT) panel."""
    try:
        import wx  # noqa: F401
    except ImportError:
        print("Simulation UI requires wxPython (run inside KiCad or install wx).")
        return

    path = Path(project_path) if project_path else _default_project_path()
    if path is None:
        print("No project path. Pass a .kicad_pro path or open a board in KiCad.")
        return

    from ui.launcher import show_simulation_dialog

    show_simulation_dialog(path)


if __name__ == "__main__":
    (
        arg_path,
        include,
        url_fetch,
        quiet,
        retry_failed,
        ui_datasheets,
        ui_chat,
        ui_simulation,
        ai_datasheets,
        ai_datasheets_auto_fetch,
        reset_datasheets,
        ask,
    ) = _parse_cli_args(sys.argv[1:])
    if ui_datasheets:
        main_ui_datasheets(arg_path, retry_failed_urls=retry_failed, ai_datasheets=ai_datasheets)
    elif ui_chat:
        main_ui_chat(arg_path, retry_failed_urls=retry_failed)
    elif ui_simulation:
        main_ui_simulation(arg_path)
    elif ask:
        main_ask(
            arg_path,
            ask,
            include_image=include,
            datasheet_url_fetch=url_fetch,
            retry_failed_urls=retry_failed,
            verbose=not quiet,
        )
    else:
        main(
            arg_path,
            include_image=include,
            datasheet_url_fetch=url_fetch,
            retry_failed_urls=retry_failed,
            datasheet_ai_discovery=ai_datasheets,
            datasheet_ai_discovery_auto_fetch=ai_datasheets_auto_fetch,
            reset_datasheets=reset_datasheets or None,
            verbose=not quiet,
        )
