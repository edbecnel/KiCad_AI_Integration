"""Stretch-slice context collection orchestrator."""

from __future__ import annotations

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
    resolver = DatasheetResolver(cfg, store, verbose=verbose)
    resolutions = resolver.resolve_all(
        symbols, project_info, retry_failed_urls=retry_failed_urls
    )

    _sync_catalog_references(store, pro_path, resolutions, symbols)

    manifest = Manifest.load(pro_path)
    manifest_path = manifest.save()

    ctx = ProjectContext(
        project_path=str(pro_path),
        project_name=pro_path.stem,
        schematics=[p.name for p in schematic_paths],
        symbols=symbols,
        datasheet_resolutions=resolutions,
        artifact_manifest_path=str(manifest_path),
    )

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
        except (KicadCliNotFoundError, PdftoppmNotFoundError, SchematicExportError):
            pass

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
