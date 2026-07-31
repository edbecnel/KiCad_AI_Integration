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

``--ui`` opens the KiCad AI Assistant launcher (project picker, context refresh, panel shortcuts).

``--ui-datasheets`` opens the Missing Required Datasheets wxPython panel (requires wx; use inside KiCad or a wx-enabled Python).

``--ui-chat`` opens the KiCad AI chat panel with context preview and Approve & Send (requires wx).

``--ui-simulation`` opens the Simulation models (SUBCKT) wxPython panel.

``--ui-aerf`` opens the AERF staged analysis panel (per-stage Approve & Send).

``--ui-notebook`` opens the Engineering Notebook panel (view/edit EKM sections).

``--ui-notebook-panel`` opens the Engineering Notebook as a non-modal frame (KiCad embedding path).

``--aerf-plan`` prints stage-0 AERF dry-run bundle and token estimate (no cloud send).

``--aerf-stage N`` builds the AERF prompt for stage N; requires ``--approve-send`` to call the provider.

``--aerf-family ID`` circuit family for AERF (default: classify or blocking_oscillator).

``--approve-send`` explicitly allow cloud transmission (AERF stages only; ``--ask`` bypasses UI separately).

``--aerf-pipeline`` runs AERF stages 0–7 sequentially; combine with ``--approve-send`` for cloud calls.

``--aerf-writeback-plan`` prints the planned EKM diff from stage outputs (no disk write).

``--aerf-stages-json PATH`` JSON file of parsed AERF stage envelopes for write-back planning.

``--approve-ekm-writeback`` persist approved stage outputs to EKM (separate gate from ``--approve-send``).

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
    bool,
    bool,
    bool,
    bool,
    bool,
    int | None,
    str | None,
    bool,
    bool,
    bool,
    str | None,
    bool,
    bool,
    list[str],
    str | None,
]:
    project_path: str | None = None
    include_image = False
    url_fetch: DatasheetUrlFetchPolicy | None = None
    quiet = False
    retry_failed = False
    ui_datasheets = False
    ui_chat = False
    ui_simulation = False
    ui_aerf = False
    ui_notebook = False
    ui_notebook_panel = False
    ui_launcher = False
    aerf_plan = False
    aerf_stage: int | None = None
    aerf_family: str | None = None
    approve_send = False
    aerf_pipeline = False
    aerf_writeback_plan = False
    aerf_stages_json: str | None = None
    approve_ekm_writeback = False
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
        elif arg == "--ui-aerf":
            ui_aerf = True
        elif arg == "--ui-notebook":
            ui_notebook = True
        elif arg == "--ui-notebook-panel":
            ui_notebook_panel = True
        elif arg == "--ui":
            ui_launcher = True
        elif arg == "--aerf-plan":
            aerf_plan = True
        elif arg == "--aerf-stage":
            if i + 1 >= len(argv):
                raise SystemExit("--aerf-stage requires a stage number 0–7")
            aerf_stage = int(argv[i + 1])
            i += 1
        elif arg == "--aerf-family":
            if i + 1 >= len(argv):
                raise SystemExit("--aerf-family requires a family_id")
            aerf_family = argv[i + 1]
            i += 1
        elif arg == "--approve-send":
            approve_send = True
        elif arg == "--aerf-pipeline":
            aerf_pipeline = True
        elif arg == "--aerf-writeback-plan":
            aerf_writeback_plan = True
        elif arg == "--aerf-stages-json":
            if i + 1 >= len(argv):
                raise SystemExit("--aerf-stages-json requires a JSON file path")
            aerf_stages_json = argv[i + 1]
            i += 1
        elif arg == "--approve-ekm-writeback":
            approve_ekm_writeback = True
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
        ui_aerf,
        ui_notebook,
        ui_notebook_panel,
        ui_launcher,
        aerf_plan,
        aerf_stage,
        aerf_family,
        approve_send,
        aerf_pipeline,
        aerf_writeback_plan,
        aerf_stages_json,
        approve_ekm_writeback,
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


def _print_writeback_plan(plan) -> None:
    print(f"--- AERF EKM write-back plan ---")
    print(plan.summary)
    for field_plan in plan.field_plans:
        print(
            f"  [{field_plan.action}] {field_plan.section_id}/{field_plan.field_id} "
            f"({field_plan.field_type}): {field_plan.value_preview}"
        )


def main_aerf_writeback_plan(
    project_path: str | Path | None,
    *,
    stages_json: str | None = None,
    approve_ekm_writeback: bool = False,
) -> None:
    """Print or apply EKM write-back from AERF stage JSON envelopes."""
    import json

    from ekm import plan_aerf_writeback, write_aerf_stages_to_ekm

    path = Path(project_path) if project_path else _default_project_path()
    if path is None:
        print("KiCad AI Assistant: no project path.")
        return
    if not stages_json:
        print("Provide --aerf-stages-json PATH with parsed AERF stage envelopes.")
        return

    stage_outputs = json.loads(Path(stages_json).read_text(encoding="utf-8"))
    if not isinstance(stage_outputs, list):
        raise SystemExit("--aerf-stages-json must contain a JSON array of stage envelopes")

    if approve_ekm_writeback:
        plan, saved = write_aerf_stages_to_ekm(path, stage_outputs, approve=True)
        _print_writeback_plan(plan)
        print(f"\nEKM saved: {saved}")
        return

    plan = plan_aerf_writeback(stage_outputs)
    _print_writeback_plan(plan)
    print("\nUse --approve-ekm-writeback to persist to engineering_knowledge.json.")


def main_aerf_pipeline(
    project_path: str | Path | None,
    *,
    family_id: str | None = None,
    approve_send: bool = False,
    approve_ekm_writeback: bool = False,
    aerf_writeback_plan: bool = False,
    include_image: bool = False,
    datasheet_url_fetch: DatasheetUrlFetchPolicy | None = None,
    retry_failed_urls: bool = False,
    verbose: bool = True,
) -> None:
    """Run AERF stages 0–7; optional EKM write-back after completion."""
    from inference.aerf import run_aerf_pipeline, run_aerf_pipeline_and_writeback

    ctx = _collect_ctx_for_aerf(
        project_path,
        include_image=include_image,
        datasheet_url_fetch=datasheet_url_fetch,
        retry_failed_urls=retry_failed_urls,
        verbose=verbose,
    )
    if ctx is None:
        return

    path = Path(project_path) if project_path else _default_project_path()
    if path is None:
        print("KiCad AI Assistant: no project path.")
        return

    if approve_ekm_writeback or aerf_writeback_plan:
        result = run_aerf_pipeline_and_writeback(
            ctx,
            path,
            family_id=family_id,
            approve_send=approve_send,
            approve_ekm_writeback=approve_ekm_writeback,
        )
        pipeline = result.pipeline
        if aerf_writeback_plan or approve_ekm_writeback:
            _print_writeback_plan(result.writeback_plan)
        if result.ekm_path is not None:
            print(f"\nEKM saved: {result.ekm_path}")
    else:
        pipeline = run_aerf_pipeline(
            ctx,
            family_id=family_id,
            approve_send=approve_send,
        )

    print(f"--- AERF pipeline ---")
    print(f"Family: {pipeline.family_id}")
    print(f"Completed stages: {len(pipeline.completed_stages)}")
    if pipeline.failed_at_stage is not None:
        print(f"Failed at stage {pipeline.failed_at_stage}: {pipeline.parse_error}")
    if not approve_send:
        print("\nDry-run only (no cloud send). Use --approve-send to call the provider.")
    elif not aerf_writeback_plan and not approve_ekm_writeback:
        print("\nUse --aerf-writeback-plan to preview EKM write-back from completed stages.")


def main_ui_notebook(project_path: str | Path | None = None) -> None:
    """Open the Engineering Notebook panel."""
    try:
        import wx  # noqa: F401
    except ImportError:
        print("Engineering Notebook UI requires wxPython (run inside KiCad or install wx).")
        return

    path = Path(project_path) if project_path else _default_project_path()
    if path is None:
        print("No project path. Pass a .kicad_pro path or open a board in KiCad.")
        return

    from ui.launcher import show_notebook_dialog

    show_notebook_dialog(path)


def main_ui_notebook_panel(project_path: str | Path | None = None) -> None:
    """Open the Engineering Notebook as a non-modal frame."""
    try:
        import wx  # noqa: F401
    except ImportError:
        print("Engineering Notebook UI requires wxPython (run inside KiCad or install wx).")
        return

    path = Path(project_path) if project_path else _default_project_path()
    if path is None:
        print("No project path. Pass a .kicad_pro path or open a board in KiCad.")
        return

    from ui.launcher import show_notebook_panel

    show_notebook_panel(path)


def main_ui_aerf(
    project_path: str | Path | None = None,
    *,
    retry_failed_urls: bool = False,
    force_refresh_urls: bool = False,
) -> None:
    """Open the AERF staged analysis panel."""
    try:
        import wx  # noqa: F401
    except ImportError:
        print("AERF UI requires wxPython (run inside KiCad or install wx).")
        return

    path = Path(project_path) if project_path else _default_project_path()
    if path is None:
        print("No project path. Pass a .kicad_pro path or open a board in KiCad.")
        return

    from ui.launcher import show_aerf_dialog

    show_aerf_dialog(
        path,
        retry_failed_urls=retry_failed_urls,
        force_refresh_urls=force_refresh_urls,
    )


def main_ui_launcher(project_path: str | Path | None = None) -> None:
    """Open the KiCad AI Assistant launcher (project picker + panels)."""
    try:
        import wx  # noqa: F401
    except ImportError:
        print("Launcher UI requires wxPython (run inside KiCad or install wx).")
        return

    from ui.launcher import show_launcher_dialog

    show_launcher_dialog(project_path)


def _collect_ctx_for_aerf(
    project_path: str | Path | None,
    *,
    include_image: bool = False,
    datasheet_url_fetch: DatasheetUrlFetchPolicy | None = None,
    retry_failed_urls: bool = False,
    verbose: bool = True,
):
    from context.model import ProjectContext

    path = Path(project_path) if project_path else _default_project_path()
    if path is None:
        print("KiCad AI Assistant: no project path.")
        return None
    cfg = load_config()
    ctx = collect_stretch_context(
        path,
        config=cfg,
        include_image=include_image,
        datasheet_url_fetch=datasheet_url_fetch,
        retry_failed_urls=retry_failed_urls,
        verbose=verbose,
    )
    return ctx


def main_aerf_plan(
    project_path: str | Path | None,
    *,
    family_id: str | None = None,
    include_image: bool = False,
    datasheet_url_fetch: DatasheetUrlFetchPolicy | None = None,
    retry_failed_urls: bool = False,
    verbose: bool = True,
) -> None:
    """Print AERF stage-0 dry-run bundle (no cloud send)."""
    from inference.aerf import build_stage0_bundle, build_aerf_stage_prompt_bundle

    ctx = _collect_ctx_for_aerf(
        project_path,
        include_image=include_image,
        datasheet_url_fetch=datasheet_url_fetch,
        retry_failed_urls=retry_failed_urls,
        verbose=verbose,
    )
    if ctx is None:
        return

    bundle = build_stage0_bundle(ctx, family_id, preview_chars=300)
    _plan, built = build_aerf_stage_prompt_bundle(
        ctx,
        bundle.family_id,
        0,
        include_image=include_image,
    )
    print(f"--- AERF plan (stage 0) ---")
    print(f"Project: {bundle.design_summary['project_name']}")
    print(f"Family: {bundle.family_id}")
    if bundle.classification:
        print(
            f"Classification: {bundle.classification.confidence} "
            f"({', '.join(bundle.classification.recognition_basis)})"
        )
    print(f"KB excerpt ({bundle.stage_plan.kb_excerpt_chars} chars):")
    print(bundle.kb_excerpt_preview)
    print(f"\nPrompt template: {built.template}")
    print(f"Estimated tokens: ~{built.estimated_text_tokens}")
    print(f"\n{built.preview_summary}")


def main_aerf_stage(
    project_path: str | Path | None,
    stage_id: int,
    *,
    family_id: str | None = None,
    approve_send: bool = False,
    include_image: bool = False,
    datasheet_url_fetch: DatasheetUrlFetchPolicy | None = None,
    retry_failed_urls: bool = False,
    verbose: bool = True,
) -> None:
    """Build or send one AERF stage prompt."""
    from inference.aerf import build_aerf_stage_prompt_bundle, run_aerf_stage

    ctx = _collect_ctx_for_aerf(
        project_path,
        include_image=include_image,
        datasheet_url_fetch=datasheet_url_fetch,
        retry_failed_urls=retry_failed_urls,
        verbose=verbose,
    )
    if ctx is None:
        return

    resolved_family = family_id
    if resolved_family is None:
        from inference.aerf import build_stage0_bundle

        bundle = build_stage0_bundle(ctx)
        resolved_family = bundle.family_id

    if not approve_send:
        plan, built = build_aerf_stage_prompt_bundle(
            ctx,
            resolved_family,
            stage_id,
            include_image=include_image,
        )
        print(f"--- AERF stage {stage_id} (dry-run, no cloud send) ---")
        print(f"Family: {resolved_family}")
        print(f"KB: {plan.kb_excerpt_path}")
        print(f"Template: {built.template}")
        print(f"Estimated tokens: ~{built.estimated_text_tokens}")
        print(f"\n{built.preview_summary}")
        print("\nUse --approve-send to transmit to the provider.")
        return

    run = run_aerf_stage(
        ctx,
        resolved_family,
        stage_id,
        include_image=include_image,
        approve_send=True,
    )
    if run.send is None:
        print("No send result (internal error).")
        return
    print(f"--- AERF stage {stage_id} response ---")
    print(run.send.response.text)
    if run.send.parse_error:
        print(f"\nParse error: {run.send.parse_error}")
    print(
        f"\nTokens: {run.send.response.usage.input_tokens} in, "
        f"{run.send.response.usage.output_tokens} out "
        f"({run.send.response.model})"
    )


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
        ui_aerf,
        ui_notebook,
        ui_notebook_panel,
        ui_launcher,
        aerf_plan,
        aerf_stage,
        aerf_family,
        approve_send,
        aerf_pipeline,
        aerf_writeback_plan,
        aerf_stages_json,
        approve_ekm_writeback,
        ai_datasheets,
        ai_datasheets_auto_fetch,
        reset_datasheets,
        ask,
    ) = _parse_cli_args(sys.argv[1:])
    if ui_launcher:
        main_ui_launcher(arg_path)
    elif ui_datasheets:
        main_ui_datasheets(arg_path, retry_failed_urls=retry_failed, ai_datasheets=ai_datasheets)
    elif ui_chat:
        main_ui_chat(arg_path, retry_failed_urls=retry_failed)
    elif ui_simulation:
        main_ui_simulation(arg_path)
    elif ui_aerf:
        main_ui_aerf(arg_path, retry_failed_urls=retry_failed)
    elif ui_notebook:
        main_ui_notebook(arg_path)
    elif ui_notebook_panel:
        main_ui_notebook_panel(arg_path)
    elif aerf_plan:
        main_aerf_plan(
            arg_path,
            family_id=aerf_family,
            include_image=include,
            datasheet_url_fetch=url_fetch,
            retry_failed_urls=retry_failed,
            verbose=not quiet,
        )
    elif aerf_pipeline:
        main_aerf_pipeline(
            arg_path,
            family_id=aerf_family,
            approve_send=approve_send,
            approve_ekm_writeback=approve_ekm_writeback,
            aerf_writeback_plan=aerf_writeback_plan,
            include_image=include,
            datasheet_url_fetch=url_fetch,
            retry_failed_urls=retry_failed,
            verbose=not quiet,
        )
    elif aerf_writeback_plan:
        main_aerf_writeback_plan(
            arg_path,
            stages_json=aerf_stages_json,
            approve_ekm_writeback=approve_ekm_writeback,
        )
    elif aerf_stage is not None:
        main_aerf_stage(
            arg_path,
            aerf_stage,
            family_id=aerf_family,
            approve_send=approve_send,
            include_image=include,
            datasheet_url_fetch=url_fetch,
            retry_failed_urls=retry_failed,
            verbose=not quiet,
        )
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
