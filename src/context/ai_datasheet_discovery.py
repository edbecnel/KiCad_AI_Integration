"""
AI datasheet discovery — Phase 1 (opt-in step 8).

Uses Claude Messages API with structured JSON URL suggestions from part number
and symbol context. No live web search (Option A MVP). Manufacturer heuristics
and URL quality filters run before AI suggestions; hallucinated portal URLs are
dropped; users get manual fallback when fetch fails.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from context.artifacts.ai_discovery_log import AiDiscoveryOutcome
from context.artifacts.catalog import ComponentRef
from context.artifacts.store import ArtifactStore, ProjectContextInfo
from context.datasheet_url_candidates import (
    heuristic_datasheet_urls,
    merge_url_candidates,
    reject_datasheet_url,
)
from context.datasheet_requirements import classify_datasheet_requirement
from context.datasheet_resolver import (
    DatasheetResolution,
    DatasheetResolver,
    normalize_datasheet_url,
)
from context.schematic_parse import SymbolInstance
from prompts.templates.datasheet_discovery import build_datasheet_discovery_prompt
from providers.base import BaseProvider
from providers.factory import get_provider
from providers.errors import ProviderError
from utils.config import AppConfig
from utils.url_fetch import UrlFetchError, fetch_url_to_file, validate_url


@dataclass
class DiscoveryResult:
    part: str
    outcome: AiDiscoveryOutcome
    suggested_urls: list[str]
    selected_url: str | None
    error: str | None
    artifact_id: str | None = None
    fetch_attempts: list[tuple[str, str | None]] = field(default_factory=list)


def _log(message: str, *, verbose: bool) -> None:
    if verbose:
        print(message, file=sys.stderr, flush=True)


def _parse_urls_from_response(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    # Try fenced JSON block first
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        brace = re.search(r"\{.*\}", text, re.DOTALL)
        if brace:
            text = brace.group(0)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    urls = data.get("urls") if isinstance(data, dict) else None
    if not isinstance(urls, list):
        return []
    return [str(u).strip() for u in urls if isinstance(u, str) and u.strip()]


def _validate_suggested_urls(urls: list[str]) -> list[str]:
    valid: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        if reject_datasheet_url(url):
            continue
        try:
            validate_url(url)
        except UrlFetchError:
            continue
        valid.append(url)
    return valid


def _symbol_datasheet_url(symbol: SymbolInstance) -> str | None:
    ds = (symbol.datasheet or "").strip()
    if ds.startswith("https://"):
        return ds
    return None


def _last_fetch_error(
    store: ArtifactStore,
    part: str,
    symbol_url: str | None,
) -> str | None:
    if not symbol_url:
        return None
    norm = normalize_datasheet_url(symbol_url)
    entry = store.url_fetch_log.get(part, norm)
    if entry is None or entry.status != "failed":
        return None
    return entry.error


def _build_symbol_context(
    symbol: SymbolInstance,
    references: list[str],
    *,
    symbol_url: str | None,
    fetch_error: str | None,
) -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "value": symbol.value or symbol.reference,
        "references": references,
        "reference_count": len(references),
        "footprint": symbol.footprint,
        "lib_id": symbol.lib_id,
        "custom_fields": dict(symbol.custom_fields),
    }
    if symbol_url:
        ctx["symbol_datasheet_url"] = symbol_url
    if fetch_error:
        ctx["last_fetch_error"] = fetch_error
    return ctx


def _is_eligible(
    symbol: SymbolInstance,
    resolution: DatasheetResolution,
) -> bool:
    if resolution.status == "resolved":
        return False
    if resolution.needs_ai_datasheet_discovery:
        return True
    requirement = classify_datasheet_requirement(symbol)
    return requirement == "required" and resolution.status in ("fetch_failed", "missing")


def _group_eligible_parts(
    symbols: list[SymbolInstance],
    resolutions: dict[str, DatasheetResolution],
    *,
    only_parts: set[str] | None = None,
) -> dict[str, tuple[SymbolInstance, list[str], DatasheetResolution]]:
    grouped: dict[str, tuple[SymbolInstance, list[str], DatasheetResolution]] = {}
    for sym in symbols:
        res = resolutions.get(sym.reference)
        if res is None or not _is_eligible(sym, res):
            continue
        part = (sym.value or sym.reference).strip()
        if only_parts is not None and part not in only_parts:
            continue
        if part in grouped:
            grouped[part][1].append(sym.reference)
            continue
        grouped[part] = (sym, [sym.reference], res)
    return grouped


def _suggest_urls(
    symbol_context: dict[str, Any],
    config: AppConfig,
    provider: BaseProvider | None,
) -> tuple[list[str], str | None]:
    user_prompt, system_prompt = build_datasheet_discovery_prompt(
        symbol_context,
        max_urls=config.datasheet_ai_discovery_max_urls,
    )
    prov = provider or get_provider(config)
    try:
        response = prov.send_message(user_prompt, system=system_prompt, config=config)
    except ProviderError as exc:
        return [], str(exc)
    urls = _parse_urls_from_response(response.text)
    return urls, None


def format_fetch_attempts_summary(
    attempts: list[tuple[str, str | None]],
    *,
    suggested_urls: list[str] | None = None,
) -> str:
    """Human-readable report of automated download attempts."""
    lines: list[str] = []
    if attempts:
        lines.append("Automated download attempts:")
        for url, err in attempts:
            if err is None:
                lines.append(f"  OK: {url}")
            else:
                lines.append(f"  FAIL: {url}")
                lines.append(f"        {err}")
    not_tried = []
    if suggested_urls:
        tried = {u for u, _ in attempts}
        not_tried = [u for u in suggested_urls if u not in tried]
    if not_tried:
        lines.append("Not attempted (open in browser manually):")
        for url in not_tried:
            lines.append(f"  {url}")
    if not lines:
        return "No download attempts recorded."
    lines.append("")
    lines.append(
        "Tip: select a URL below (or use Open URL), download in your browser, "
        "then Attach PDF… for this part Value."
    )
    return "\n".join(lines)


def _try_fetch_and_register(
    url: str,
    part: str,
    symbol: SymbolInstance,
    project: ProjectContextInfo,
    store: ArtifactStore,
    config: AppConfig,
    resolver: DatasheetResolver,
    fetch_fn: Callable[..., object],
) -> tuple[str | None, str | None]:
    norm_url = normalize_datasheet_url(url)
    component_ref = ComponentRef(reference=symbol.reference, sheet_path=symbol.sheet_path)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        read_timeout = min(config.url_fetch_read_timeout_sec, 25)
        fetch_fn(
            url,
            tmp_path,
            timeout_sec=config.url_fetch_timeout_sec,
            read_timeout_sec=read_timeout,
            warmup=config.url_fetch_warmup,
        )
        artifact_id, _ = resolver._register_and_link(  # noqa: SLF001
            tmp_path,
            part,
            "ai_discovery",
            project,
            component_ref,
            source_url=norm_url,
        )
        store.url_fetch_log.record_downloaded(part, norm_url, artifact_id=artifact_id)
        return artifact_id, None
    except (UrlFetchError, OSError) as exc:
        store.url_fetch_log.record_failed(part, norm_url, error=str(exc))
        return None, str(exc)
    finally:
        if tmp_path.is_file():
            tmp_path.unlink(missing_ok=True)


def _download_url_list(
    urls: list[str],
    *,
    part: str,
    symbol: SymbolInstance,
    project: ProjectContextInfo,
    store: ArtifactStore,
    config: AppConfig,
    resolver: DatasheetResolver,
    fetch: Callable[..., object],
    should_cancel: Callable[[], bool] | None,
    on_part_status: Callable[[str, str], None] | None,
    on_fetch_attempt: Callable[[str, str, str | None], None] | None,
) -> tuple[bool, str | None, str | None, list[tuple[str, str | None]]]:
    """Try each URL in order. Returns (downloaded, artifact_id, last_error, attempts)."""
    fetch_attempts: list[tuple[str, str | None]] = []
    last_error: str | None = None
    artifact_id: str | None = None
    selected: str | None = None
    total = len(urls)

    for index, url in enumerate(urls, start=1):
        if should_cancel and should_cancel():
            break
        selected = url
        status = f"Downloading URL {index}/{total}…"
        if on_part_status:
            on_part_status(part, status)
        _log(f"  Downloading {url}", verbose=True)
        artifact_id, last_error = _try_fetch_and_register(
            url,
            part,
            symbol,
            project,
            store,
            config,
            resolver,
            fetch,
        )
        if artifact_id is not None:
            fetch_attempts.append((url, None))
            if on_fetch_attempt:
                on_fetch_attempt(part, url, None)
            return True, artifact_id, url, fetch_attempts
        fetch_attempts.append((url, last_error))
        if on_fetch_attempt:
            on_fetch_attempt(part, url, last_error)
        _log(f"  Fetch failed: {last_error}", verbose=True)

    return False, None, selected, fetch_attempts


def run_ai_datasheet_discovery(
    symbols: list[SymbolInstance],
    resolutions: dict[str, DatasheetResolution],
    project: ProjectContextInfo,
    store: ArtifactStore,
    config: AppConfig,
    *,
    provider: BaseProvider | None = None,
    fetch_fn: Callable[..., object] | None = None,
    approve_url: Callable[[str, list[str]], str | None] | None = None,
    on_part_status: Callable[[str, str], None] | None = None,
    on_fetch_attempt: Callable[[str, str, str | None], None] | None = None,
    only_parts: set[str] | None = None,
    should_cancel: Callable[[], bool] | None = None,
    verbose: bool = True,
) -> dict[str, DiscoveryResult]:
    """
    Run opt-in AI datasheet discovery for eligible parts (deduped by Value).

    ``approve_url(part, urls)`` returns the URL to fetch, or None to skip/reject.
    When ``datasheet_ai_discovery_auto_fetch`` is True, the first valid URL is used.
    When auto_fetch is False and no ``approve_url`` callback is provided (headless CLI),
  suggested URLs are logged but not downloaded.
    """
    if not config.datasheet_ai_discovery:
        return {}

    fetch = fetch_fn or fetch_url_to_file
    resolver = DatasheetResolver(config, store, fetch_fn=fetch, verbose=False)
    grouped = _group_eligible_parts(symbols, resolutions, only_parts=only_parts)
    results: dict[str, DiscoveryResult] = {}
    attempted: set[str] = set()

    for part, (symbol, refs, _res) in grouped.items():
        if should_cancel and should_cancel():
            break
        if part in attempted:
            continue
        attempted.add(part)

        if on_part_status:
            on_part_status(part, "Searching with AI…")

        symbol_url = _symbol_datasheet_url(symbol)
        fetch_error = _last_fetch_error(store, part, symbol_url)
        context = _build_symbol_context(
            symbol,
            refs,
            symbol_url=symbol_url,
            fetch_error=fetch_error,
        )

        _log(f"AI datasheet discovery: {part} ({len(refs)} ref(s))", verbose=verbose)
        raw_urls, provider_error = _suggest_urls(context, config, provider)
        heuristic_urls = heuristic_datasheet_urls(part, context)
        if heuristic_urls:
            _log(f"  Heuristic URL candidates: {heuristic_urls}", verbose=verbose)
        merged_urls = merge_url_candidates(heuristic_urls, raw_urls)

        valid_urls = _validate_suggested_urls(merged_urls)[
            : config.datasheet_ai_discovery_max_urls
        ]
        if not valid_urls:
            error = provider_error or "No valid direct PDF URLs (heuristic or AI)"
            store.ai_discovery_log.record_attempt(
                part,
                symbol_datasheet_url=symbol_url,
                suggested_urls=merged_urls,
                outcome="no_url_found",
                error=error,
            )
            results[part] = DiscoveryResult(
                part=part,
                outcome="no_url_found",
                suggested_urls=merged_urls,
                selected_url=None,
                error=error,
            )
            continue

        last_error: str | None = None
        downloaded = False
        selected: str | None = None
        artifact_id: str | None = None
        user_rejected = False
        fetch_attempts: list[tuple[str, str | None]] = []

        if config.datasheet_ai_discovery_auto_fetch:
            downloaded, artifact_id, selected, fetch_attempts = _download_url_list(
                valid_urls,
                part=part,
                symbol=symbol,
                project=project,
                store=store,
                config=config,
                resolver=resolver,
                fetch=fetch,
                should_cancel=should_cancel,
                on_part_status=on_part_status,
                on_fetch_attempt=on_fetch_attempt,
            )
        elif approve_url is not None:
            if on_part_status:
                on_part_status(part, "Waiting for URL approval…")
            chosen = approve_url(part, valid_urls)
            if chosen is None:
                user_rejected = True
            else:
                urls_to_try = [chosen] + [u for u in valid_urls if u != chosen]
                downloaded, artifact_id, selected, fetch_attempts = _download_url_list(
                    urls_to_try,
                    part=part,
                    symbol=symbol,
                    project=project,
                    store=store,
                    config=config,
                    resolver=resolver,
                    fetch=fetch,
                    should_cancel=should_cancel,
                    on_part_status=on_part_status,
                    on_fetch_attempt=on_fetch_attempt,
                )
            if user_rejected and not downloaded:
                store.ai_discovery_log.record_attempt(
                    part,
                    symbol_datasheet_url=symbol_url,
                    suggested_urls=valid_urls,
                    outcome="user_rejected",
                    error="User declined download",
                )
                results[part] = DiscoveryResult(
                    part=part,
                    outcome="user_rejected",
                    suggested_urls=valid_urls,
                    selected_url=selected,
                    error="User declined download",
                )
                continue
        else:
            store.ai_discovery_log.record_attempt(
                part,
                symbol_datasheet_url=symbol_url,
                suggested_urls=valid_urls,
                outcome="no_url_found",
                error=(
                    "AI suggested URLs (fetch not attempted — enable "
                    "--ai-datasheets-auto-fetch or use Missing datasheets panel)"
                ),
            )
            results[part] = DiscoveryResult(
                part=part,
                outcome="no_url_found",
                suggested_urls=valid_urls,
                selected_url=None,
                error=(
                    "AI suggested URLs (fetch not attempted — enable "
                    "--ai-datasheets-auto-fetch or use Missing datasheets panel)"
                ),
            )
            continue

        if downloaded:
            store.ai_discovery_log.record_attempt(
                part,
                symbol_datasheet_url=symbol_url,
                suggested_urls=valid_urls,
                selected_url=selected,
                outcome="downloaded",
                artifact_id=artifact_id,
                fetch_attempts=fetch_attempts,
            )
            results[part] = DiscoveryResult(
                part=part,
                outcome="downloaded",
                suggested_urls=valid_urls,
                selected_url=selected,
                error=None,
                artifact_id=artifact_id,
                fetch_attempts=fetch_attempts,
            )
        elif not user_rejected:
            last_error = fetch_attempts[-1][1] if fetch_attempts else "Download failed"
            summary_error = format_fetch_attempts_summary(
                fetch_attempts,
                suggested_urls=valid_urls,
            )
            store.ai_discovery_log.record_attempt(
                part,
                symbol_datasheet_url=symbol_url,
                suggested_urls=valid_urls,
                selected_url=selected,
                outcome="fetch_failed",
                error=last_error or "Download failed",
                fetch_attempts=fetch_attempts,
            )
            results[part] = DiscoveryResult(
                part=part,
                outcome="fetch_failed",
                suggested_urls=valid_urls,
                selected_url=selected,
                error=summary_error,
                fetch_attempts=fetch_attempts,
            )

    return results
