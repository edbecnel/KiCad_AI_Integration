"""Headless helpers for missing-datasheet UI and attach workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from context.artifacts.store import ArtifactStore, ProjectContextInfo
from context.collector import collect_stretch_context
from context.datasheet_requirements import summarize_required_missing_datasheets
from context.datasheet_resolver import DatasheetResolver
from context.model import ProjectContext
from context.schematic_parse import SymbolInstance
from utils.config import AppConfig, load_config


@dataclass
class MissingDatasheetRow:
    """One unresolved part Value grouped across schematic references."""

    part: str
    references: list[str]
    reference_count: int
    status: str
    errors: list[str]
    symbol_datasheet_url: str | None = None

    @classmethod
    def from_summary_entry(cls, entry: dict[str, object], symbols: list[SymbolInstance]) -> MissingDatasheetRow:
        part = str(entry["part"])
        refs = list(entry.get("references") or [])
        url: str | None = None
        for sym in symbols:
            if (sym.value or sym.reference) == part and sym.datasheet.startswith("https://"):
                url = sym.datasheet
                break
        errors = entry.get("errors")
        return cls(
            part=part,
            references=refs,
            reference_count=int(entry.get("reference_count") or len(refs)),
            status=str(entry.get("status") or "missing"),
            errors=list(errors) if isinstance(errors, list) else [],
            symbol_datasheet_url=url,
        )


def collect_project_context(
    project_path: Path,
    *,
    config: AppConfig | None = None,
    retry_failed_urls: bool = False,
    verbose: bool = False,
) -> ProjectContext:
    """Run stretch context collection (symbols + datasheet resolutions)."""
    return collect_stretch_context(
        project_path,
        config=config,
        retry_failed_urls=retry_failed_urls,
        verbose=verbose,
    )


def get_missing_datasheet_rows(
    project_path: Path,
    *,
    config: AppConfig | None = None,
    retry_failed_urls: bool = False,
    verbose: bool = False,
) -> tuple[ProjectContext, list[MissingDatasheetRow]]:
    """Collect context and return grouped missing required datasheet rows."""
    ctx = collect_project_context(
        project_path,
        config=config,
        retry_failed_urls=retry_failed_urls,
        verbose=verbose,
    )
    summary = summarize_required_missing_datasheets(ctx.symbols, ctx.datasheet_resolutions)
    rows = [MissingDatasheetRow.from_summary_entry(entry, ctx.symbols) for entry in summary]
    return ctx, rows


def attach_datasheet_pdf(
    project_path: Path,
    part: str,
    pdf_path: Path,
    *,
    config: AppConfig | None = None,
    verbose: bool = False,
) -> ProjectContext:
    """
    Register a user-selected PDF for all symbols matching ``part`` (Value).

    Uses ``resolve_symbol(..., user_attach_path=...)`` for one reference per Value;
    sha256 dedupe links the same artifact to sibling references on refresh.
    """
    cfg = config or load_config()
    ctx = collect_project_context(project_path, config=cfg, verbose=verbose)
    pro_path = Path(ctx.project_path)
    project_info = ProjectContextInfo(
        project_pro_path=pro_path,
        schematic_paths=[pro_path.parent / name for name in ctx.schematics],
    )
    store = ArtifactStore(cfg.artifact_library_path)
    resolver = DatasheetResolver(cfg, store, verbose=verbose)

    target: SymbolInstance | None = None
    for sym in ctx.symbols:
        if (sym.value or sym.reference) == part:
            target = sym
            break
    if target is None:
        raise ValueError(f"No symbol with Value {part!r} in project")

    resolver.resolve_symbol(target, project_info, user_attach_path=pdf_path.expanduser())

    return collect_project_context(project_path, config=cfg, verbose=verbose)


def manual_pdf_path_for_part(library_path: Path, part: str) -> Path:
    """Canonical manual drop path: ``datasheets/{Value}.pdf``."""
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in part.strip())
    return library_path.expanduser() / "datasheets" / f"{safe or 'unknown_part'}.pdf"


def format_row_manual_instructions(row: MissingDatasheetRow, library_path: Path) -> str:
    """Short manual-supply hint for a missing row (UI tooltip or status line)."""
    manual_path = manual_pdf_path_for_part(library_path, row.part)
    lines = [f"Attach PDF for {row.part}, or save as:", str(manual_path)]
    if row.symbol_datasheet_url:
        lines.insert(0, f"Symbol URL: {row.symbol_datasheet_url}")
    if row.errors:
        lines.insert(0, f"Failed: {row.errors[0]}")
    return "\n".join(lines)
