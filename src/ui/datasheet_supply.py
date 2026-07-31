"""Headless helpers for missing-datasheet UI and attach workflow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from context.artifacts.catalog import ComponentRef
from context.artifacts.manifest import Manifest
from context.artifacts.store import ArtifactDeletionError, ArtifactStore, ProjectContextInfo
from context.collector import _resolve_project_file, collect_stretch_context
from context.datasheet_requirements import (
    summarize_required_datasheets,
    summarize_required_missing_datasheets,
)
from context.datasheet_resolver import normalize_datasheet_url
from context.model import ProjectContext
from context.schematic_parse import SymbolInstance, discover_schematic_paths, parse_project_schematics
from context.schematic_write import (
    DatasheetFieldWriteResult,
    summarize_symbol_field_issues,
    write_resolved_datasheet_urls,
)
from utils.config import AppConfig, load_config


@dataclass
class MissingDatasheetRow:
    """One part Value grouped across schematic references."""

    part: str
    references: list[str]
    reference_count: int
    status: str
    errors: list[str]
    symbol_datasheet_url: str | None = None
    suggested_urls: list[str] = field(default_factory=list)
    discovery_outcome: str | None = None
    discovery_error: str | None = None
    selected_url: str | None = None
    discovery_status: str = ""
    artifact_id: str | None = None
    local_path: str | None = None
    is_resolved: bool = False
    sources_tried: list[str] = field(default_factory=list)
    field_issue: str = ""
    field_issue_label: str = ""
    field_issue_detail: str = ""
    symbol_fields: list[str] = field(default_factory=list)
    resolved_url: str | None = None
    fetch_attempts: list[tuple[str, str | None]] = field(default_factory=list)

    @classmethod
    def from_field_issue_entry(
        cls,
        entry: dict[str, object],
        symbols: list[SymbolInstance],
    ) -> MissingDatasheetRow:
        part = str(entry["part"])
        issue = str(entry.get("field_issue") or "")
        from context.schematic_write import FIELD_ISSUE_LABELS

        label = FIELD_ISSUE_LABELS.get(issue, issue)  # type: ignore[arg-type]
        row = cls.from_summary_entry(entry, symbols)
        row.field_issue = issue
        row.field_issue_label = label
        row.field_issue_detail = str(entry.get("field_issue_detail") or "")
        row.symbol_fields = list(entry.get("symbol_fields") or [])
        row.resolved_url = (
            str(entry["resolved_url"]) if entry.get("resolved_url") else None
        )
        row.discovery_status = label
        return row

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
        suggested = entry.get("suggested_urls")
        discovery_outcome = entry.get("discovery_outcome")
        discovery_error = entry.get("discovery_error")
        selected_url = entry.get("selected_url")
        fetch_attempts_raw = entry.get("fetch_attempts")
        fetch_attempts: list[tuple[str, str | None]] = []
        if isinstance(fetch_attempts_raw, list):
            for item in fetch_attempts_raw:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    fetch_attempts.append((str(item[0]), item[1]))
                elif isinstance(item, dict) and item.get("url"):
                    fetch_attempts.append((str(item["url"]), item.get("error")))
        status = str(entry.get("status") or "missing")
        discovery_status = _discovery_status_label(
            status,
            discovery_outcome=str(discovery_outcome) if discovery_outcome else None,
        )
        if entry.get("is_resolved"):
            discovery_status = "resolved"
        sources = entry.get("sources_tried")
        return cls(
            part=part,
            references=refs,
            reference_count=int(entry.get("reference_count") or len(refs)),
            status=status,
            errors=list(errors) if isinstance(errors, list) else [],
            symbol_datasheet_url=url,
            suggested_urls=list(suggested) if isinstance(suggested, list) else [],
            discovery_outcome=str(discovery_outcome) if discovery_outcome else None,
            discovery_error=str(discovery_error) if discovery_error else None,
            selected_url=str(selected_url) if selected_url else None,
            discovery_status=discovery_status,
            artifact_id=str(entry["artifact_id"]) if entry.get("artifact_id") else None,
            local_path=str(entry["local_path"]) if entry.get("local_path") else None,
            is_resolved=bool(entry.get("is_resolved")),
            sources_tried=list(sources) if isinstance(sources, list) else [],
            fetch_attempts=fetch_attempts,
        )


def _discovery_status_label(
    resolver_status: str,
    *,
    discovery_outcome: str | None,
) -> str:
    if discovery_outcome == "downloaded":
        return "Resolved"
    if discovery_outcome in ("fetch_failed", "no_url_found", "user_rejected"):
        return "Failed — attach manually"
    return resolver_status


def _is_stale_fetch_not_attempted_error(error: str | None) -> bool:
    return bool(error and "fetch not attempted" in error)


def enrich_rows_from_discovery_log(
    rows: list[MissingDatasheetRow],
    store: ArtifactStore,
    *,
    current_results: dict[str, object] | None = None,
) -> None:
    """Fill row discovery fields from the latest log entry when not in the current run."""
    current = current_results or {}
    for row in rows:
        if row.part in current:
            continue
        entry = store.ai_discovery_log.get_latest(row.part)
        if entry is None:
            continue
        if not row.suggested_urls and entry.suggested_urls:
            row.suggested_urls = list(entry.suggested_urls)
        if not row.discovery_outcome:
            row.discovery_outcome = entry.outcome
        if not row.selected_url and entry.selected_url:
            row.selected_url = entry.selected_url
        if not row.discovery_error and entry.error:
            row.discovery_error = entry.error
        if not row.fetch_attempts and entry.fetch_attempts:
            row.fetch_attempts = [
                (str(a["url"]), a.get("error")) for a in entry.fetch_attempts
            ]
        if _is_stale_fetch_not_attempted_error(row.discovery_error) and row.suggested_urls:
            row.discovery_status = "AI URL ready"
        elif row.discovery_outcome:
            row.discovery_status = _discovery_status_label(
                row.status,
                discovery_outcome=row.discovery_outcome,
            )


def build_missing_rows_from_context(
    ctx: ProjectContext,
    *,
    config: AppConfig | None = None,
) -> list[MissingDatasheetRow]:
    """Build missing-datasheet rows from an existing ProjectContext (no re-collection)."""
    cfg = config or load_config()
    summary = summarize_required_missing_datasheets(
        ctx.symbols,
        ctx.datasheet_resolutions,
        ai_discovery_results=ctx.ai_discovery_results,
    )
    rows = [MissingDatasheetRow.from_summary_entry(entry, ctx.symbols) for entry in summary]
    store = ArtifactStore(cfg.artifact_library_path)
    enrich_rows_from_discovery_log(rows, store, current_results=ctx.ai_discovery_results)
    return rows


def build_required_rows_from_context(
    ctx: ProjectContext,
    *,
    config: AppConfig | None = None,
) -> list[MissingDatasheetRow]:
    """Build all required-datasheet rows from an existing ProjectContext."""
    cfg = config or load_config()
    summary = summarize_required_datasheets(
        ctx.symbols,
        ctx.datasheet_resolutions,
        ai_discovery_results=ctx.ai_discovery_results,
    )
    rows = [MissingDatasheetRow.from_summary_entry(entry, ctx.symbols) for entry in summary]
    store = ArtifactStore(cfg.artifact_library_path)
    enrich_rows_from_discovery_log(rows, store, current_results=ctx.ai_discovery_results)
    return rows


def build_field_issue_rows_from_context(
    ctx: ProjectContext,
    *,
    config: AppConfig | None = None,
) -> list[MissingDatasheetRow]:
    """Build symbol-field issue rows from an existing ProjectContext."""
    cfg = config or load_config()
    store = ArtifactStore(cfg.artifact_library_path)
    summary = summarize_symbol_field_issues(
        ctx.symbols,
        ctx.datasheet_resolutions,
        store,
        ctx.ai_discovery_results,
    )
    return [
        MissingDatasheetRow.from_field_issue_entry(entry, ctx.symbols) for entry in summary
    ]


def format_row_detail_text(row: MissingDatasheetRow, *, max_length: int | None = None) -> str:
    """Human-readable detail for a datasheet row (full text unless max_length set)."""
    from context.ai_datasheet_discovery import format_fetch_attempts_summary

    detail_parts: list[str] = []
    if row.fetch_attempts:
        detail_parts.append(
            format_fetch_attempts_summary(
                row.fetch_attempts,
                suggested_urls=row.suggested_urls or None,
            )
        )
    elif row.discovery_error and not _is_stale_fetch_not_attempted_error(row.discovery_error):
        detail_parts.append(row.discovery_error)
    elif row.errors:
        detail_parts.append(row.errors[0])
    if row.sources_tried:
        detail_parts.append("via: " + ", ".join(row.sources_tried[-4:]))
    if row.symbol_datasheet_url:
        detail_parts.append(f"Symbol: {row.symbol_datasheet_url}")
    if not row.fetch_attempts:
        for url in row.suggested_urls[:3]:
            if url != row.symbol_datasheet_url:
                detail_parts.append(f"Suggested: {url}")
        if row.selected_url and row.selected_url not in row.suggested_urls:
            detail_parts.append(f"Selected: {row.selected_url}")
    text = "\n".join(detail_parts) if row.fetch_attempts else " | ".join(detail_parts)
    if max_length is not None and len(text) > max_length:
        return text[: max_length - 1] + "…"
    return text


def collect_project_context(
    project_path: Path,
    *,
    config: AppConfig | None = None,
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
    verbose: bool = False,
) -> ProjectContext:
    """Run stretch context collection (symbols + datasheet resolutions)."""
    return collect_stretch_context(
        project_path,
        config=config,
        retry_failed_urls=retry_failed_urls,
        force_refresh_urls=force_refresh_urls,
        force_refresh_parts=force_refresh_parts,
        datasheet_ai_discovery=datasheet_ai_discovery,
        datasheet_ai_discovery_auto_fetch=datasheet_ai_discovery_auto_fetch,
        approve_ai_datasheet_url=approve_ai_datasheet_url,
        on_datasheet_status=on_datasheet_status,
        on_fetch_attempt=on_fetch_attempt,
        ai_discovery_only_parts=ai_discovery_only_parts,
        ai_discovery_should_cancel=ai_discovery_should_cancel,
        verbose=verbose,
    )


def get_missing_datasheet_rows(
    project_path: Path,
    *,
    config: AppConfig | None = None,
    retry_failed_urls: bool = False,
    force_refresh_urls: bool = False,
    datasheet_ai_discovery: bool | None = False,
    datasheet_ai_discovery_auto_fetch: bool | None = None,
    approve_ai_datasheet_url: Callable[[str, list[str]], str | None] | None = None,
    verbose: bool = False,
) -> tuple[ProjectContext, list[MissingDatasheetRow]]:
    """Collect context and return grouped missing required datasheet rows.

    AI discovery runs only when ``datasheet_ai_discovery`` is True. Default False
    so refresh/list loads do not trigger headless discovery without URL approval.
    Pass ``datasheet_ai_discovery=None`` to honor ``datasheet_ai_discovery`` in config.
    """
    ctx = collect_project_context(
        project_path,
        config=config,
        retry_failed_urls=retry_failed_urls,
        force_refresh_urls=force_refresh_urls,
        datasheet_ai_discovery=datasheet_ai_discovery,
        datasheet_ai_discovery_auto_fetch=datasheet_ai_discovery_auto_fetch,
        approve_ai_datasheet_url=approve_ai_datasheet_url,
        verbose=verbose,
    )
    rows = build_missing_rows_from_context(ctx, config=config)
    return ctx, rows


def get_required_datasheet_rows(
    project_path: Path,
    *,
    config: AppConfig | None = None,
    verbose: bool = False,
) -> tuple[ProjectContext, list[MissingDatasheetRow]]:
    """Collect context and return all datasheet-required parts (resolved and missing)."""
    ctx = collect_project_context(
        project_path,
        config=config,
        verbose=verbose,
        datasheet_ai_discovery=False,
    )
    rows = build_required_rows_from_context(ctx, config=config)
    return ctx, rows


def get_symbol_field_issue_rows(
    project_path: Path,
    *,
    config: AppConfig | None = None,
    verbose: bool = False,
) -> tuple[ProjectContext, list[MissingDatasheetRow]]:
    """Required parts whose schematic Datasheet property is empty or incorrect."""
    ctx = collect_project_context(
        project_path,
        config=config,
        verbose=verbose,
        datasheet_ai_discovery=False,
    )
    rows = build_field_issue_rows_from_context(ctx, config=config)
    return ctx, rows


def _quarantine_local_pdf_file(pdf_path: Path) -> Path | None:
    if not pdf_path.is_file():
        return None
    dest_dir = pdf_path.parent / ".quarantine"
    dest_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = dest_dir / f"{pdf_path.stem}-{ts}.pdf"
    pdf_path.rename(dest)
    return dest


def reset_datasheet_for_part(
    project_path: Path,
    part: str,
    *,
    config: AppConfig | None = None,
    delete_orphan_artifact: bool = False,
    quarantine_local_pdf: bool | None = None,
    rerun_ai_discovery: bool | None = None,
    approve_ai_datasheet_url: Callable[[str, list[str]], str | None] | None = None,
    on_status: Callable[[str], None] | None = None,
    verbose: bool = False,
) -> ProjectContext:
    """
    Reset cached datasheet resolution for a part Value and re-resolve from scratch.

    Unlinks project manifest/catalog references, clears ``url_fetch_log`` entries for
    the part, optionally quarantines ``datasheets/{Value}.pdf``, then runs the resolver
    with ``force_refresh_parts`` so catalog/manifest/local-PDF fallbacks are bypassed.
    """
    part_norm = part.strip()
    if not part_norm:
        raise ValueError("part Value must be non-empty")

    cfg = config or load_config()
    pro_path = _resolve_project_file(project_path)
    schematic_paths = discover_schematic_paths(pro_path)
    symbols = parse_project_schematics(
        pro_path.parent,
        schematic_paths,
        root_schematic=schematic_paths[0] if schematic_paths else None,
    )
    matching = [s for s in symbols if (s.value or s.reference).strip() == part_norm]
    if not matching:
        raise ValueError(f"No symbol with Value {part_norm!r} in project")

    if on_status:
        on_status(f"Clearing cached links for {part_norm}…")

    project_info = ProjectContextInfo(
        project_pro_path=pro_path,
        schematic_paths=schematic_paths,
    )
    store = ArtifactStore(cfg.artifact_library_path)
    store.bootstrap_project(pro_path)

    manifest = Manifest.load(pro_path)
    artifact_ids: set[str] = set(manifest.remove_links_for_part(part_norm))
    for entry in store.get_by_part(part_norm, "datasheet"):
        artifact_ids.add(entry.id)

    project_path_str = project_info.project_path
    for sym in matching:
        for aid in list(artifact_ids):
            store.catalog.remove_component_reference(
                aid,
                project_path_str,
                sym.reference,
                sym.sheet_path,
            )
    for aid in list(artifact_ids):
        cat_entry = store.catalog.get_by_id(aid)
        if cat_entry is None:
            continue
        cat_entry.referenced_by = [
            p for p in cat_entry.referenced_by if p.project_path != project_path_str
        ]
        store.catalog.update_artifact(cat_entry)
    manifest.save()

    store.url_fetch_log.remove_entries_for_part(part_norm)
    store.url_fetch_log.save()

    do_quarantine = (
        cfg.datasheet_reset_quarantine_local_pdf
        if quarantine_local_pdf is None
        else quarantine_local_pdf
    )
    if do_quarantine:
        _quarantine_local_pdf_file(manual_pdf_path_for_part(cfg.artifact_library_path, part_norm))

    if delete_orphan_artifact:
        for aid in artifact_ids:
            if store.catalog.can_delete(aid):
                try:
                    store.delete_artifact(aid)
                except ArtifactDeletionError:
                    pass

    run_ai = cfg.datasheet_ai_discovery if rerun_ai_discovery is None else rerun_ai_discovery

    if on_status:
        if run_ai:
            on_status(f"Re-resolving {part_norm} (URL fetch, then AI if needed)…")
        else:
            on_status(f"Re-resolving {part_norm} (URL fetch)…")

    ctx = collect_project_context(
        project_path,
        config=cfg,
        retry_failed_urls=True,
        force_refresh_parts={part_norm},
        datasheet_ai_discovery=bool(run_ai),
        approve_ai_datasheet_url=approve_ai_datasheet_url,
        on_datasheet_status=on_status,
        ai_discovery_only_parts={part_norm} if run_ai else None,
        verbose=verbose,
    )
    if cfg.datasheet_write_symbol_url:
        maybe_write_datasheet_urls_to_schematic(
            pro_path,
            ctx,
            store,
            config=cfg,
            part=part_norm,
        )
    return ctx


def run_ai_discovery_for_rows(
    project_path: Path,
    *,
    config: AppConfig | None = None,
    only_parts: set[str] | None = None,
    should_cancel: Callable[[], bool] | None = None,
    approve_ai_datasheet_url: Callable[[str, list[str]], str | None] | None = None,
    on_part_status: Callable[[str, str], None] | None = None,
    on_fetch_attempt: Callable[[str, str, str | None], None] | None = None,
    verbose: bool = False,
) -> ProjectContext:
    """Run AI discovery with URL approval (UI) or auto-fetch when configured."""
    cfg = config or load_config()

    approve: Callable[[str, list[str]], str | None] | None = None
    auto_fetch = cfg.datasheet_ai_discovery_auto_fetch
    if auto_fetch:
        approve = None
    elif approve_ai_datasheet_url is not None:

        def _approve(part: str, urls: list[str]) -> str | None:
            if on_part_status:
                on_part_status(part, "Choose AI URL…")
            chosen = approve_ai_datasheet_url(part, urls)
            if chosen and on_part_status:
                on_part_status(part, "Downloading…")
            return chosen

        approve = _approve
    else:
        raise ValueError(
            "AI datasheet discovery requires approve_ai_datasheet_url or "
            "datasheet_ai_discovery_auto_fetch in config"
        )

    def _bridge_status(message: str) -> None:
        if on_part_status and ": " in message:
            part, detail = message.split(": ", 1)
            on_part_status(part, detail)

    return collect_project_context(
        project_path,
        config=cfg,
        datasheet_ai_discovery=True,
        datasheet_ai_discovery_auto_fetch=auto_fetch,
        approve_ai_datasheet_url=approve,
        on_datasheet_status=_bridge_status if on_part_status else None,
        on_fetch_attempt=on_fetch_attempt,
        ai_discovery_only_parts=only_parts,
        ai_discovery_should_cancel=should_cancel,
        verbose=verbose,
    )


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

    Copies the file into ``datasheets/{Value}.pdf``, updates catalog + manifest,
    and clears stale per-part fetch failures so refresh shows resolved.
    """
    part_norm = part.strip()
    if not part_norm:
        raise ValueError("part Value must be non-empty")

    source = pdf_path.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"PDF not found: {source}")

    cfg = config or load_config()
    pro_path = _resolve_project_file(project_path)
    schematic_paths = discover_schematic_paths(pro_path)
    symbols = parse_project_schematics(
        pro_path.parent,
        schematic_paths,
        root_schematic=schematic_paths[0] if schematic_paths else None,
    )
    matching = [
        sym
        for sym in symbols
        if (sym.value or sym.reference).strip() == part_norm
    ]
    if not matching:
        raise ValueError(f"No symbol with Value {part_norm!r} in project")

    project_info = ProjectContextInfo(
        project_pro_path=pro_path,
        schematic_paths=schematic_paths,
    )
    store = ArtifactStore(cfg.artifact_library_path)
    store.bootstrap_project(pro_path)

    for entry in list(store.get_by_part(part_norm, "datasheet")):
        if store.resolve_local_path(entry.id) is None and store.catalog.can_delete(entry.id):
            try:
                store.delete_artifact(entry.id)
            except ArtifactDeletionError:
                pass

    manifest = Manifest.load(pro_path)
    manifest.remove_links_for_part(part_norm)
    manifest.save()

    first = matching[0]
    source_url: str | None = None
    for sym in matching:
        if sym.datasheet.startswith("https://"):
            source_url = normalize_datasheet_url(sym.datasheet)
            break
    entry = store.register_datasheet(
        source,
        part_norm,
        "user_attach",
        project_info,
        ComponentRef(
            reference=first.reference,
            sheet_path=first.sheet_path,
            sheet_name=first.sheet_name,
        ),
        source_url=source_url,
    )
    for sym in matching[1:]:
        store.link_existing(
            entry.id,
            project_info,
            ComponentRef(
                reference=sym.reference,
                sheet_path=sym.sheet_path,
                sheet_name=sym.sheet_name,
            ),
            part=part_norm,
        )

    store.url_fetch_log.remove_entries_for_part(part_norm)
    for sym in matching:
        if sym.datasheet.startswith("https://"):
            store.url_fetch_log.record_downloaded(
                part_norm,
                normalize_datasheet_url(sym.datasheet),
                artifact_id=entry.id,
            )
    store.url_fetch_log.save()

    if verbose:
        dest = store.resolve_local_path(entry.id)
        print(f"Attached {source.name} → {dest}", file=__import__("sys").stderr)

    ctx = collect_project_context(project_path, config=cfg, verbose=verbose)
    if cfg.datasheet_write_symbol_url:
        maybe_write_datasheet_urls_to_schematic(
            pro_path,
            ctx,
            store,
            config=cfg,
            part=part_norm,
        )
    return ctx


def maybe_write_datasheet_urls_to_schematic(
    project_pro_path: Path,
    ctx: ProjectContext,
    store: ArtifactStore | None = None,
    *,
    config: AppConfig | None = None,
    part: str | None = None,
    only_if_empty: bool = False,
) -> DatasheetFieldWriteResult | None:
    """Write resolved HTTPS URLs to schematic symbols when enabled in config."""
    cfg = config or load_config()
    if not cfg.datasheet_write_symbol_url:
        return None
    pro_path = project_pro_path.expanduser().resolve()
    artifact_store = store or ArtifactStore(cfg.artifact_library_path)
    return write_resolved_datasheet_urls(
        pro_path,
        ctx,
        artifact_store,
        part=part,
        only_if_empty=only_if_empty,
    )


def format_write_url_success_message(result: DatasheetFieldWriteResult) -> str:
    """User-facing alert after a successful Write URL to schematic action."""
    refs = ", ".join(u.reference for u in result.updated)
    url = result.updated[0].new_url
    sheets = sorted({u.sheet_path for u in result.updated})
    sheet_lines = "\n".join(f"  • {name}" for name in sheets)
    return (
        f"Updated symbol Datasheet field(s): {refs}\n\n"
        f"{url}\n\n"
        f"Schematic file(s):\n{sheet_lines}\n\n"
        "If a sheet is open in KiCad's Schematic Editor, the Datasheet property "
        "will not update on screen until you reload from disk.\n\n"
        "To see the change without losing your work:\n"
        "1. Save the schematic in KiCad first if you have unsaved edits you want "
        "to keep.\n"
        "2. Do not use File → Save after this write — that can overwrite the new "
        "URL with the old value still shown in the editor.\n"
        "3. In the Schematic Editor: File → Revert on the sheet(s) above, or "
        "close and reopen that schematic.\n\n"
        "File → Revert discards schematic changes made since your last save."
    )


def manual_pdf_path_for_part(library_path: Path, part: str) -> Path:
    """Canonical manual drop path: ``datasheets/{Value}.pdf``."""
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in part.strip())
    return library_path.expanduser() / "datasheets" / f"{safe or 'unknown_part'}.pdf"


def format_row_manual_instructions(row: MissingDatasheetRow, library_path: Path) -> str:
    """Short manual-supply hint for a missing row (UI tooltip or status line)."""
    manual_path = manual_pdf_path_for_part(library_path, row.part)
    lines: list[str] = []
    if row.discovery_error:
        lines.append(f"Failed: {row.discovery_error}")
    elif row.errors:
        lines.append(f"Failed: {row.errors[0]}")
    if row.symbol_datasheet_url:
        lines.append(f"Symbol URL: {row.symbol_datasheet_url}")
    for url in row.suggested_urls[:3]:
        if url != row.symbol_datasheet_url:
            lines.append(f"Suggested URL: {url}")
    if row.local_path:
        lines.append(f"Current PDF: {row.local_path}")
    lines.extend([f"Attach PDF for {row.part}, or save as:", str(manual_path)])
    return "\n".join(lines)
