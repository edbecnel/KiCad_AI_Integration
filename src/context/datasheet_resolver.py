"""Datasheet resolution for symbols — six-step priority chain."""

from __future__ import annotations

import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal
from urllib.parse import unquote, urlparse

from context.artifacts.catalog import ComponentRef
from context.artifacts.manifest import Manifest
from context.artifacts.store import ArtifactStore, ProjectContextInfo
from context.schematic_parse import SymbolInstance
from utils.config import AppConfig
from utils.url_fetch import UrlFetchError, fetch_url_to_file

ResolutionStatus = Literal["resolved", "missing", "fetch_failed"]
TierHint = Literal["A", "B", "C"]
UrlFetchOutcome = Literal["downloaded", "failed"]


@dataclass
class DatasheetResolution:
    status: ResolutionStatus = "missing"
    artifact_id: str | None = None
    local_path: Path | None = None
    tier_hint: TierHint = "C"
    sources_tried: list[str] = field(default_factory=list)
    reference: str = ""
    part: str = ""
    url_fetch_outcome: UrlFetchOutcome | None = None
    needs_ai_datasheet_discovery: bool = False


@dataclass
class _ResolveSession:
    manifest: Manifest
    url_to_artifact: dict[str, str]
    failed_urls: set[str]
    urls_attempted: set[str]
    pending_manifest_save: bool = False
    pending_url_log_save: bool = False
    retry_failed_urls: bool = False


def _normalize_file_url(value: str) -> str:
    if value.startswith("file://"):
        parsed = urlparse(value)
        return unquote(parsed.path)
    return value


def normalize_datasheet_url(url: str) -> str:
    """Canonical form for deduplicating HTTPS datasheet URLs."""
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    port = parsed.port
    netloc = host
    if port and port not in (443,):
        netloc = f"{host}:{port}"
    path = parsed.path.rstrip("/") or "/"
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{parsed.scheme.lower()}://{netloc}{path}{query}"


def _resolve_local_path(
    datasheet_field: str,
    project_root: Path,
    search_paths: list[Path],
) -> Path | None:
    if not datasheet_field or datasheet_field.startswith("http"):
        return None
    raw = _normalize_file_url(datasheet_field.strip())
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (project_root / candidate).resolve()
    if candidate.is_file():
        return candidate
    for folder in search_paths:
        alt = (folder.expanduser() / Path(raw).name).resolve()
        if alt.is_file():
            return alt
    return None


def _tier_for_symbol(symbol: SymbolInstance, resolved: bool) -> TierHint:
    if resolved:
        return "A"
    if symbol.footprint or symbol.lib_id or len(symbol.custom_fields) > 0:
        return "B"
    if symbol.value:
        return "B"
    return "C"


def _log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


class DatasheetResolver:
    """Resolve datasheet PDFs using the priority chain from Netlist Gap Fill spec."""

    def __init__(
        self,
        config: AppConfig,
        store: ArtifactStore | None = None,
        fetch_fn: Callable[..., object] | None = None,
        *,
        verbose: bool = True,
    ) -> None:
        self.config = config
        self.store = store or ArtifactStore(config.artifact_library_path)
        self.fetch_fn = fetch_fn or fetch_url_to_file
        self.verbose = verbose
        self._session: _ResolveSession | None = None

    def _link(
        self,
        artifact_id: str,
        project: ProjectContextInfo,
        component_ref: ComponentRef,
        *,
        part: str | None = None,
    ) -> None:
        assert self._session is not None
        self.store.link_existing(
            artifact_id,
            project,
            component_ref,
            part=part,
            manifest=self._session.manifest,
            save_manifest=False,
        )
        self._session.pending_manifest_save = True

    def _register_and_link(
        self,
        source_path: Path,
        part: str,
        source: str,
        project: ProjectContextInfo,
        component_ref: ComponentRef,
        *,
        source_url: str | None = None,
    ) -> tuple[str, Path | None]:
        if self._session is not None:
            entry = self.store.register_datasheet(
                source_path,
                part,
                source,
                project,
                component_ref=None,
                source_url=source_url,
            )
            self._link(entry.id, project, component_ref, part=part)
        else:
            entry = self.store.register_datasheet(
                source_path,
                part,
                source,
                project,
                component_ref,
                source_url=source_url,
            )
        return entry.id, self.store.resolve_local_path(entry.id)

    def _record_url_downloaded(
        self,
        part: str,
        norm_url: str,
        artifact_id: str,
    ) -> None:
        self.store.url_fetch_log.record_downloaded(
            part, norm_url, artifact_id=artifact_id
        )
        if self._session is not None:
            self._session.pending_url_log_save = True
            self._session.failed_urls.discard(norm_url)
        else:
            self.store.url_fetch_log.save()

    def _record_url_failed(
        self,
        part: str,
        norm_url: str,
        error: str,
    ) -> None:
        self.store.url_fetch_log.record_failed(part, norm_url, error=error)
        if self._session is not None:
            self._session.pending_url_log_save = True
            self._session.failed_urls.add(norm_url)
        else:
            self.store.url_fetch_log.save()

    def _known_failed_urls(self) -> set[str]:
        if self._session is not None:
            return self._session.failed_urls
        return self.store.url_fetch_log.failed_urls()

    def _apply_url_fetch_failure(
        self,
        resolution: DatasheetResolution,
        symbol: SymbolInstance,
        *,
        cached_id: str | None,
        cached_path: Path | None,
        source_tag: str,
        error: str | None = None,
    ) -> DatasheetResolution:
        resolution.sources_tried.append(source_tag)
        resolution.url_fetch_outcome = "failed"
        resolution.needs_ai_datasheet_discovery = True
        if cached_id is not None:
            return self._resolved(resolution, cached_id, cached_path, symbol)
        resolution.status = "fetch_failed"
        if error:
            resolution.sources_tried.append(f"fetch_error:{error}")
        resolution.tier_hint = _tier_for_symbol(symbol, False)
        return resolution

    def _resolve_from_url_log_download(
        self,
        resolution: DatasheetResolution,
        symbol: SymbolInstance,
        project: ProjectContextInfo,
        component_ref: ComponentRef,
        artifact_id: str,
    ) -> DatasheetResolution | None:
        local = self.store.resolve_local_path(artifact_id)
        if local is None:
            return None
        self._link_or_store(artifact_id, project, component_ref, part=symbol.value or symbol.reference)
        resolution.url_fetch_outcome = "downloaded"
        return self._resolved(resolution, artifact_id, local, symbol)

    def _link_or_store(
        self,
        artifact_id: str,
        project: ProjectContextInfo,
        component_ref: ComponentRef,
        *,
        part: str | None = None,
    ) -> None:
        if self._session is not None:
            self._link(artifact_id, project, component_ref, part=part)
        else:
            self.store.link_existing(artifact_id, project, component_ref, part=part)

    def _note_url_downloaded_from_cache(
        self,
        part: str,
        norm_url: str,
        artifact_id: str,
    ) -> None:
        """Ensure url_fetch_log records a prior successful download for this part+URL."""
        existing = self.store.url_fetch_log.get(part, norm_url)
        if existing is not None and existing.status == "downloaded":
            return
        self._record_url_downloaded(part, norm_url, artifact_id)

    def _part_pdf_candidates(self, part: str) -> list[Path]:
        """Local PDF paths to try for a schematic Value (part number)."""
        patterns = (f"{part}.pdf", f"{part.lower()}.pdf", f"{part.upper()}.pdf")
        folders: list[Path] = [self.store.library_path / "datasheets"]
        folders.extend(p.expanduser() for p in self.config.datasheet_search_paths)
        seen: set[Path] = set()
        candidates: list[Path] = []
        for folder in folders:
            if not folder.is_dir():
                continue
            for pattern in patterns:
                candidate = (folder / pattern).resolve()
                if candidate.is_file() and candidate not in seen:
                    seen.add(candidate)
                    candidates.append(candidate)
        return candidates

    def _try_local_part_pdf(
        self,
        resolution: DatasheetResolution,
        symbol: SymbolInstance,
        project: ProjectContextInfo,
        component_ref: ComponentRef,
        part: str,
        *,
        source: str = "library_datasheet_file",
    ) -> DatasheetResolution | None:
        for candidate in self._part_pdf_candidates(part):
            if source not in resolution.sources_tried:
                resolution.sources_tried.append(source)
            if self.verbose:
                _log(
                    f"  using local datasheet file: {candidate.name} "
                    f"for {symbol.reference} ({part})"
                )
            artifact_id, local_path = self._register_and_link(
                candidate,
                part,
                source,
                project,
                component_ref,
            )
            resolution.url_fetch_outcome = "downloaded"
            return self._resolved(resolution, artifact_id, local_path, symbol)
        return None

    def resolve_symbol(
        self,
        symbol: SymbolInstance,
        project: ProjectContextInfo,
        *,
        user_attach_path: Path | None = None,
    ) -> DatasheetResolution:
        resolution = DatasheetResolution(
            reference=symbol.reference,
            part=symbol.value or symbol.reference,
        )
        part = symbol.value or symbol.reference
        component_ref = ComponentRef(
            reference=symbol.reference,
            sheet_path=symbol.sheet_path,
            sheet_name=symbol.sheet_name,
        )
        policy = self.config.datasheet_url_fetch
        is_https = symbol.datasheet.startswith("https://")
        cached_id: str | None = None
        cached_path: Path | None = None

        def use_cached_or_continue(artifact_id: str, local: Path | None) -> bool:
            """Link cached artifact; return True if resolution is complete."""
            nonlocal cached_id, cached_path
            cached_id, cached_path = artifact_id, local
            self._link_or_store(artifact_id, project, component_ref, part=part)
            if policy == "always" and is_https:
                return False
            return True

        # 1. Shared catalog lookup by part
        resolution.sources_tried.append("catalog")
        catalog_hits = self.store.get_by_part(part, "datasheet")
        if catalog_hits:
            entry = catalog_hits[0]
            local = self.store.resolve_local_path(entry.id)
            if local is not None:
                if use_cached_or_continue(entry.id, local):
                    return self._resolved(resolution, entry.id, local, symbol)

        # 1b. Catalog lookup by HTTPS URL (cross-part dedupe)
        if is_https:
            norm_url = normalize_datasheet_url(symbol.datasheet)
            resolution.sources_tried.append("catalog_url")
            url_entry = self.store.catalog.get_by_source_url(norm_url)
            if url_entry is not None:
                local = self.store.resolve_local_path(url_entry.id)
                if local is not None:
                    self._note_url_downloaded_from_cache(part, norm_url, url_entry.id)
                    if use_cached_or_continue(url_entry.id, local):
                        resolution.url_fetch_outcome = "downloaded"
                        return self._resolved(resolution, url_entry.id, local, symbol)
            if self._session is not None and norm_url in self._session.url_to_artifact:
                artifact_id = self._session.url_to_artifact[norm_url]
                local = self.store.resolve_local_path(artifact_id)
                if local is not None:
                    self._note_url_downloaded_from_cache(part, norm_url, artifact_id)
                    if use_cached_or_continue(artifact_id, local):
                        resolution.url_fetch_outcome = "downloaded"
                        return self._resolved(resolution, artifact_id, local, symbol)

        # 2. Per-project manifest links
        resolution.sources_tried.append("project_manifest")
        manifest = (
            self._session.manifest
            if self._session is not None
            else Manifest.load(project.project_pro_path)
        )
        for link in manifest.get_links_for_part(part):
            local = self.store.resolve_local_path(link.artifact_id)
            if local is not None:
                if use_cached_or_continue(link.artifact_id, local):
                    return self._resolved(resolution, link.artifact_id, local, symbol)

        # 3. Symbol Datasheet field — local path
        if symbol.datasheet and not symbol.datasheet.startswith("http"):
            resolution.sources_tried.append("symbol_datasheet_local")
            local = _resolve_local_path(
                symbol.datasheet,
                project.project_root,
                self.config.datasheet_search_paths,
            )
            if local is not None:
                artifact_id, local_path = self._register_and_link(
                    local, part, "symbol_field", project, component_ref
                )
                return self._resolved(resolution, artifact_id, local_path, symbol)

        # 4. User attach
        if user_attach_path is not None and user_attach_path.is_file():
            resolution.sources_tried.append("user_attach")
            artifact_id, local_path = self._register_and_link(
                user_attach_path, part, "user_attach", project, component_ref
            )
            return self._resolved(resolution, artifact_id, local_path, symbol)

        # 5. Local PDF files by part Value (shared library datasheets/ + search_paths)
        # Skip when policy forces HTTPS refresh even if a local copy exists.
        if not (policy == "always" and is_https):
            resolution.sources_tried.append("library_datasheet_file")
            local_resolved = self._try_local_part_pdf(
                resolution,
                symbol,
                project,
                component_ref,
                part,
            )
            if local_resolved is not None:
                return local_resolved

        # 6. HTTPS fetch from symbol field (policy-controlled; deduped by URL)
        if is_https:
            norm_url = normalize_datasheet_url(symbol.datasheet)
            url_log = self.store.url_fetch_log.get(part, norm_url)
            if policy == "never":
                resolution.sources_tried.append("https_fetch_disabled")
                if cached_id is not None:
                    return self._resolved(resolution, cached_id, cached_path, symbol)
            elif policy == "if_missing" and cached_id is not None:
                if is_https:
                    self._note_url_downloaded_from_cache(part, norm_url, cached_id)
                resolution.url_fetch_outcome = "downloaded"
                return self._resolved(resolution, cached_id, cached_path, symbol)
            elif (
                not (self._session is not None and self._session.retry_failed_urls)
                and norm_url in self._known_failed_urls()
            ):
                resolution.sources_tried.append("url_fetch_log:failed")
                if self.verbose:
                    _log(
                        f"  url fetch skipped (failed): {symbol.reference} ({part}) "
                        f"— checking local datasheet file …"
                    )
                local_resolved = self._try_local_part_pdf(
                    resolution,
                    symbol,
                    project,
                    component_ref,
                    part,
                    source="library_datasheet_file_after_url_failed",
                )
                if local_resolved is not None:
                    return local_resolved
                if url_log is None or url_log.status == "failed":
                    self._record_url_failed(
                        part,
                        norm_url,
                        error=url_log.error if url_log else "previous attempt failed for this URL",
                    )
                return self._apply_url_fetch_failure(
                    resolution,
                    symbol,
                    cached_id=cached_id,
                    cached_path=cached_path,
                    source_tag="url_fetch_log:failed",
                    error=url_log.error if url_log else None,
                )
            elif (
                self._session is not None
                and norm_url in self._session.urls_attempted
            ):
                resolution.sources_tried.append("https_fetch_deduped")
                if self.verbose:
                    _log(
                        f"  url fetch skipped (already attempted): "
                        f"{symbol.reference} ({part})"
                    )
                local_resolved = self._try_local_part_pdf(
                    resolution,
                    symbol,
                    project,
                    component_ref,
                    part,
                    source="library_datasheet_file_after_url_failed",
                )
                if local_resolved is not None:
                    return local_resolved
                return self._apply_url_fetch_failure(
                    resolution,
                    symbol,
                    cached_id=cached_id,
                    cached_path=cached_path,
                    source_tag="url_fetch_log:failed",
                    error=url_log.error if url_log else "previous attempt failed for this URL",
                )
            elif (
                url_log is not None
                and url_log.status == "downloaded"
                and policy != "always"
            ):
                resolution.sources_tried.append("url_fetch_log:downloaded")
                if url_log.artifact_id:
                    resolved = self._resolve_from_url_log_download(
                        resolution,
                        symbol,
                        project,
                        component_ref,
                        url_log.artifact_id,
                    )
                    if resolved is not None:
                        if self.verbose:
                            _log(
                                f"  url fetch skipped (downloaded): "
                                f"{symbol.reference} ({part})"
                            )
                        return resolved
                if cached_id is not None:
                    resolution.url_fetch_outcome = "downloaded"
                    return self._resolved(resolution, cached_id, cached_path, symbol)
            elif policy in ("if_missing", "always"):
                resolution.sources_tried.append("https_fetch")
                if self._session is not None:
                    self._session.urls_attempted.add(norm_url)
                try:
                    if self.verbose:
                        action = "Refreshing" if cached_id else "Fetching"
                        _log(f"{action} datasheet: {symbol.reference} ({part}) …")
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                        tmp_path = Path(tmp.name)
                    self.fetch_fn(
                        symbol.datasheet,
                        tmp_path,
                        timeout_sec=self.config.url_fetch_timeout_sec,
                        read_timeout_sec=self.config.url_fetch_read_timeout_sec,
                        warmup=self.config.url_fetch_warmup,
                    )
                    artifact_id, local_path = self._register_and_link(
                        tmp_path,
                        part,
                        "url_fetch",
                        project,
                        component_ref,
                        source_url=norm_url,
                    )
                    tmp_path.unlink(missing_ok=True)
                    if self._session is not None:
                        self._session.url_to_artifact[norm_url] = artifact_id
                    self._record_url_downloaded(part, norm_url, artifact_id)
                    resolution.url_fetch_outcome = "downloaded"
                    if self.verbose:
                        _log(f"  downloaded {artifact_id}")
                    return self._resolved(resolution, artifact_id, local_path, symbol)
                except (UrlFetchError, OSError) as exc:
                    self._record_url_failed(part, norm_url, error=str(exc))
                    if self.verbose:
                        _log(
                            f"  url fetch failed: {symbol.reference} ({part}) — "
                            f"checking local datasheet file …"
                        )
                    local_resolved = self._try_local_part_pdf(
                        resolution,
                        symbol,
                        project,
                        component_ref,
                        part,
                        source="library_datasheet_file_after_url_failed",
                    )
                    if local_resolved is not None:
                        return local_resolved
                    if self.verbose:
                        _log(
                            f"  no local datasheet for {part} — "
                            f"needs AI datasheet discovery ({exc})"
                        )
                    return self._apply_url_fetch_failure(
                        resolution,
                        symbol,
                        cached_id=cached_id,
                        cached_path=cached_path,
                        source_tag="url_fetch_log:failed",
                        error=str(exc),
                    )

        if cached_id is not None:
            return self._resolved(resolution, cached_id, cached_path, symbol)

        resolution.status = "missing"
        resolution.tier_hint = _tier_for_symbol(symbol, False)
        return resolution

    def _resolved(
        self,
        resolution: DatasheetResolution,
        artifact_id: str,
        local_path: Path | None,
        symbol: SymbolInstance,
    ) -> DatasheetResolution:
        resolution.status = "resolved"
        resolution.artifact_id = artifact_id
        resolution.local_path = local_path
        resolution.tier_hint = _tier_for_symbol(symbol, True)
        return resolution

    def _build_url_index(self) -> dict[str, str]:
        index: dict[str, str] = {}
        for entry in self.store.catalog.artifacts:
            if entry.source_url:
                index[entry.source_url] = entry.id
        return index

    def resolve_all(
        self,
        symbols: list[SymbolInstance],
        project: ProjectContextInfo,
        *,
        retry_failed_urls: bool = False,
    ) -> dict[str, DatasheetResolution]:
        manifest = Manifest.load(project.project_pro_path)
        self.store.bootstrap()
        self._session = _ResolveSession(
            manifest=manifest,
            url_to_artifact=self._build_url_index(),
            failed_urls=(
                set()
                if retry_failed_urls
                else self.store.url_fetch_log.failed_urls()
            ),
            urls_attempted=set(),
            retry_failed_urls=retry_failed_urls,
        )
        if self.verbose:
            https_count = sum(1 for s in symbols if s.datasheet.startswith("https://"))
            retry_note = ", retry_failed_urls" if retry_failed_urls else ""
            _log(
                f"Resolving datasheets for {len(symbols)} placed symbols "
                f"({https_count} with HTTPS URLs, url_fetch={self.config.datasheet_url_fetch}{retry_note}) …"
            )
        try:
            results: dict[str, DatasheetResolution] = {}
            for sym in symbols:
                results[sym.reference] = self.resolve_symbol(sym, project)
            if self._session.pending_manifest_save:
                self._session.manifest.save()
            if self._session.pending_url_log_save:
                self.store.url_fetch_log.save()
            return results
        finally:
            self._session = None
