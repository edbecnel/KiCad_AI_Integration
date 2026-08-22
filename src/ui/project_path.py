"""Project path normalization and context summary formatting for the Assistant shell."""

from __future__ import annotations

from pathlib import Path

from context.collector import collect_stretch_context
from context.datasheet_requirements import format_required_datasheet_notice
from context.model import ProjectContext
from context.simulation_gaps import summarize_simulation_gaps
from context.artifacts.store import ArtifactStore
from prompts.builder import build_prompt_summary
from ui.launcher import resolve_project_pro_path
from utils.config import AppConfig, load_config


def normalize_launcher_project_path(text: str) -> Path:
    """Resolve a project path field to a .kicad_pro file."""
    stripped = text.strip()
    if not stripped:
        raise ValueError("Select a KiCad project (.kicad_pro) or project folder.")
    return resolve_project_pro_path(stripped)


def format_launcher_context_summary(
    project_path: Path,
    ctx: ProjectContext,
    *,
    cfg: AppConfig | None = None,
) -> str:
    """Format a human-readable status block from a collected ProjectContext."""
    resolved_cfg = cfg or load_config()
    lines = [build_prompt_summary(ctx, include_image=False)]

    notice = format_required_datasheet_notice(
        ctx.symbols,
        ctx.datasheet_resolutions,
        library_path=resolved_cfg.artifact_library_path,
        ai_discovery_results=ctx.ai_discovery_results,
    )
    if notice:
        lines.append("")
        lines.append(notice)

    pro = Path(project_path).expanduser().resolve()
    project_root = pro.parent
    sim_rows = summarize_simulation_gaps(
        ctx.symbols,
        project_root=project_root,
        resolutions=ctx.datasheet_resolutions,
        store=ArtifactStore(resolved_cfg.artifact_library_path),
        netlist_text=(
            str(ctx.netlist_summary.get("text"))
            if ctx.netlist_summary and ctx.netlist_summary.get("text")
            else None
        ),
        missing_only=True,
    )
    if sim_rows:
        lines.append("")
        lines.append("--- Simulation models missing ---")
        for row in sim_rows[:12]:
            lines.append(f"  {row.part} ({', '.join(row.references)}): {row.gap_detail}")
        if len(sim_rows) > 12:
            lines.append(f"  … and {len(sim_rows) - 12} more")

    return "\n".join(lines)


def build_launcher_context_summary(project_path: Path) -> str:
    """Collect project context and format a human-readable status block."""
    cfg = load_config()
    ctx = collect_stretch_context(project_path, config=cfg, verbose=False)
    return format_launcher_context_summary(project_path, ctx, cfg=cfg)
