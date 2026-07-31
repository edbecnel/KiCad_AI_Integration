"""Stretch-slice context collection orchestrator."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from context.artifacts.manifest import Manifest
from context.artifacts.store import ArtifactStore, ProjectContextInfo
from context.datasheet_resolver import DatasheetResolver
from context.model import ProjectContext
from context.schematic_image import (
    KicadCliNotFoundError,
    PdftoppmNotFoundError,
    SchematicExportError,
    export_schematic_image,
)
from context.schematic_connectivity import connectivity_summary, parse_project_labels
from context.schematic_parse import (
    discover_schematic_paths,
    parse_project_schematics,
)
from utils.config import AppConfig, DatasheetUrlFetchPolicy, load_config


def collect_stretch_context(
    project_path: Path,
    *,
    config: AppConfig | None = None,
    include_image: bool = False,
    fetch_datasheet_urls: bool | None = None,
    datasheet_url_fetch: DatasheetUrlFetchPolicy | None = None,
    retry_failed_urls: bool = False,
    force_refresh_urls: bool = False,
    force_refresh_parts: set[str] | None = None,
    datasheet_ai_discovery: bool | None = None,
    datasheet_ai_discovery_auto_fetch: bool | None = None,
    approve_ai_datasheet_url: Callable[[str, list[str]], str | None] | None = None,
    on_datasheet_status: Callable[[str], None] | None = None,
    on_fetch_attempt: Callable[[str, str, str | None], None] | None = None,
    ai_discovery_only_parts: set[str] | None = None,
    ai_discovery_should_cancel: Callable[[], bool] | None = None,
    verbose: bool = True,
) -> ProjectContext:
    """
    Collect stretch-slice context: symbols, datasheet resolutions, optional schematic PNG.

    project_path may be a .kicad_pro file or project directory containing one.
    """
    cfg = config or load_config()
    if datasheet_url_fetch is not None:
        cfg.datasheet_url_fetch = datasheet_url_fetch
    elif fetch_datasheet_urls is not None:
        cfg.datasheet_url_fetch = "if_missing" if fetch_datasheet_urls else "never"
    if force_refresh_urls:
        cfg.datasheet_url_fetch = "always"
    if datasheet_ai_discovery is not None:
        cfg.datasheet_ai_discovery = datasheet_ai_discovery
    if datasheet_ai_discovery_auto_fetch is not None:
        cfg.datasheet_ai_discovery_auto_fetch = datasheet_ai_discovery_auto_fetch
    pro_path = _resolve_project_file(project_path)
    schematic_paths = discover_schematic_paths(pro_path)
    project_root = pro_path.parent

    symbols = parse_project_schematics(
        project_root,
        schematic_paths,
        root_schematic=schematic_paths[0] if schematic_paths else None,
    )

    project_info = ProjectContextInfo(
        project_pro_path=pro_path,
        schematic_paths=schematic_paths,
    )
    store = ArtifactStore(cfg.artifact_library_path)
    store.bootstrap_project(pro_path)
    store.scan_datasheets_folder()
    resolver = DatasheetResolver(cfg, store, verbose=verbose)
    refresh_parts = {p.strip() for p in (force_refresh_parts or set())}
    resolutions = resolver.resolve_all(
        symbols,
        project_info,
        retry_failed_urls=retry_failed_urls or force_refresh_urls or bool(refresh_parts),
        force_refresh_parts=refresh_parts,
    )

    ai_discovery_results: dict = {}
    if cfg.datasheet_ai_discovery:
        from context.ai_datasheet_discovery import run_ai_datasheet_discovery

        ai_discovery_results = run_ai_datasheet_discovery(
            symbols,
            resolutions,
            project_info,
            store,
            cfg,
            approve_url=approve_ai_datasheet_url,
            on_part_status=(
                (lambda part, msg: on_datasheet_status(f"{part}: {msg}"))
                if on_datasheet_status
                else None
            ),
            on_fetch_attempt=on_fetch_attempt,
            only_parts=ai_discovery_only_parts,
            should_cancel=ai_discovery_should_cancel,
            verbose=verbose,
        )
        if any(r.outcome == "downloaded" for r in ai_discovery_results.values()):
            resolutions = resolver.resolve_all(
                symbols,
                project_info,
                retry_failed_urls=retry_failed_urls or force_refresh_urls or bool(refresh_parts),
                force_refresh_parts=refresh_parts,
            )
        store.url_fetch_log.save()
        store.ai_discovery_log.save()

    _sync_catalog_references(store, pro_path, resolutions, symbols)

    if cfg.spice_write_symbol_fields:
        from context.schematic_write import apply_builtin_simulation_models

        builtin_result = apply_builtin_simulation_models(pro_path, symbols)
        if builtin_result.changed_count:
            symbols = parse_project_schematics(
                project_root,
                schematic_paths,
                root_schematic=schematic_paths[0] if schematic_paths else None,
            )

    manifest = Manifest.load(pro_path)
    manifest_path = manifest.save()

    ctx = ProjectContext(
        project_path=str(pro_path),
        project_name=pro_path.stem,
        schematics=[p.name for p in schematic_paths],
        symbols=symbols,
        datasheet_resolutions=resolutions,
        artifact_manifest_path=str(manifest_path),
        ai_discovery_results=ai_discovery_results,
    )

    labels = parse_project_labels(project_root, schematic_paths)
    if labels:
        ctx.schematic_connectivity = connectivity_summary(labels)

    from context.pcb_summary import collect_pcb_summary
    from context.netlist_export import collect_netlist_summary

    ctx.pcb_summary = collect_pcb_summary(pro_path)
    ctx.netlist_summary = collect_netlist_summary(pro_path, config=cfg)

    if include_image and schematic_paths:
        exports_dir = project_root / "kicad_ai" / "exports"
        try:
            png_bytes, meta = export_schematic_image(
                schematic_paths[0],
                dpi=cfg.schematic_image_dpi,
                output_dir=exports_dir,
                kicad_cli=cfg.kicad_cli,
            )
            ctx.schematic_image = png_bytes
            ctx.schematic_image_meta = meta
        except (KicadCliNotFoundError, PdftoppmNotFoundError, SchematicExportError) as exc:
            ctx.schematic_image_error = str(exc)

    return ctx


def _resolve_project_file(project_path: Path) -> Path:
    path = project_path.expanduser().resolve()
    if path.is_file() and path.suffix == ".kicad_pro":
        return path
    if path.is_dir():
        pros = sorted(path.glob("*.kicad_pro"))
        if len(pros) == 1:
            return pros[0]
        if pros:
            return pros[0]
        raise FileNotFoundError(f"No .kicad_pro found in {path}")
    raise FileNotFoundError(f"Invalid project path: {project_path}")


def _sync_catalog_references(
    store: ArtifactStore,
    pro_path: Path,
    resolutions: dict,
    symbols: list,
) -> None:
    from context.artifacts.catalog import ComponentRef

    active: dict[str, list[ComponentRef]] = {}
    for sym in symbols:
        res = resolutions.get(sym.reference)
        if res is None or res.artifact_id is None:
            continue
        active.setdefault(res.artifact_id, []).append(
            ComponentRef(
                reference=sym.reference,
                sheet_path=sym.sheet_path,
                sheet_name=sym.sheet_name,
            )
        )
    store.catalog.sync_project_references(str(pro_path.resolve()), active)
