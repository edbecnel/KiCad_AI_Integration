"""Layer-aware partial context refresh for multi-turn chat."""

from __future__ import annotations

from pathlib import Path

from context.collector import _resolve_project_file
from context.context_flags import ContextIncludeFlags
from context.fingerprint import (
    ProjectFingerprint,
    compute_fingerprint,
    dirty_layers,
    load_fingerprint,
    save_fingerprint,
)
from context.model import ProjectContext
from context.schematic_connectivity import (
    build_pin_connectivity,
    connectivity_summary,
    parse_project_labels,
    parse_project_pins,
)
from context.schematic_parse import discover_schematic_paths, parse_project_schematics
from utils.config import AppConfig, load_config

# Map UI include flags to fingerprint layer names.
FLAG_TO_LAYERS: dict[str, tuple[str, ...]] = {
    "schematic": ("schematic", "bom", "datasheets"),
    "pcb": ("pcb",),
    "bom": ("bom", "schematic"),
    "erc_drc": ("erc_drc",),
    "netlist": ("netlist",),
}


def layers_for_flags(flags: ContextIncludeFlags) -> set[str]:
    """Expand ``ContextIncludeFlags`` to fingerprint layer names."""
    selected: set[str] = set()
    if flags.schematic:
        selected.update(FLAG_TO_LAYERS["schematic"])
    if flags.pcb:
        selected.update(FLAG_TO_LAYERS["pcb"])
    if flags.bom:
        selected.update(FLAG_TO_LAYERS["bom"])
    if flags.erc_drc:
        selected.update(FLAG_TO_LAYERS["erc_drc"])
    if flags.netlist:
        selected.update(FLAG_TO_LAYERS["netlist"])
    return selected


def detect_dirty_layers(
    project_path: Path | str,
    *,
    previous: ProjectFingerprint | None = None,
) -> set[str]:
    """Return fingerprint layers that changed since ``previous`` (or disk cache)."""
    stored = previous if previous is not None else load_fingerprint(project_path)
    current = compute_fingerprint(project_path)
    return dirty_layers(stored, current)


def refresh_context_layers(
    ctx: ProjectContext,
    project_path: Path | str,
    layers: set[str],
    *,
    config: AppConfig | None = None,
    include_image: bool = False,
) -> ProjectContext:
    """Re-collect only the requested layers into an existing ``ProjectContext``."""
    if not layers:
        return ctx

    cfg = config or load_config()
    pro = _resolve_project_file(Path(project_path))
    project_root = pro.parent
    schematic_paths = discover_schematic_paths(pro)

    if "schematic" in layers or "bom" in layers or "datasheets" in layers:
        symbols = parse_project_schematics(
            project_root,
            schematic_paths,
            root_schematic=schematic_paths[0] if schematic_paths else None,
        )
        ctx.symbols = symbols
        ctx.schematics = [p.name for p in schematic_paths]

        labels = parse_project_labels(project_root, schematic_paths)
        schematic_pins = parse_project_pins(project_root, schematic_paths)
        pin_connectivity = build_pin_connectivity(symbols, schematic_pins, ctx.connectivity_graph)
        if labels or schematic_pins:
            ctx.schematic_connectivity = connectivity_summary(
                labels,
                pin_connectivity=pin_connectivity,
            )

    if "bom" in layers:
        from context.bom_summary import build_bom_summary

        ctx.bom_summary = build_bom_summary(ctx.symbols)

    if "pcb" in layers:
        from context.pcb_summary import collect_pcb_summary

        ctx.pcb_summary = collect_pcb_summary(pro)

    if "netlist" in layers:
        from context.netlist_export import collect_netlist_summary
        from context.netlist_gap_fill import detect_connectivity_gaps
        from context.netlist_graph import build_connectivity_graph_from_summary

        ctx.netlist_summary = collect_netlist_summary(pro, config=cfg)
        ctx.connectivity_graph = build_connectivity_graph_from_summary(ctx.netlist_summary)
        schematic_pins = parse_project_pins(project_root, schematic_paths)
        pin_connectivity = build_pin_connectivity(
            ctx.symbols, schematic_pins, ctx.connectivity_graph
        )
        ctx.connectivity_gaps = detect_connectivity_gaps(
            ctx.symbols,
            pin_connectivity=pin_connectivity,
            connectivity_graph=ctx.connectivity_graph,
        )

    if "erc_drc" in layers:
        from context.erc_drc_summary import collect_erc_drc_summary

        ctx.erc_drc_summary = collect_erc_drc_summary(pro)

    if "image" in layers and include_image and schematic_paths:
        from context.schematic_image import (
            KicadCliNotFoundError,
            PdftoppmNotFoundError,
            SchematicExportError,
            export_schematic_image,
        )

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
            ctx.schematic_image_error = None
        except (KicadCliNotFoundError, PdftoppmNotFoundError, SchematicExportError) as exc:
            ctx.schematic_image_error = str(exc)

    from context.token_budget import estimate_context_tokens

    ctx.token_budget = estimate_context_tokens(ctx)
    save_fingerprint(compute_fingerprint(pro))
    return ctx
