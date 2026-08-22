"""Ad-hoc chat inference workflow (general_review template)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from context.collector import collect_stretch_context
from context.context_cache import (
    ContextCacheEntry,
    cache_matches_project,
    load_context_cache,
    save_context_cache,
)
from context.context_flags import ContextIncludeFlags
from context.incremental import (
    detect_dirty_layers,
    layers_for_flags,
    refresh_context_layers,
)
from context.model import ProjectContext
from conversation.session import ChatSession
from prompts import (
    BuiltPrompt,
    build_general_review_prompt,
    build_isolation_clearance_prompt,
    build_netlist_crosscheck_prompt,
    build_netlist_gap_fill_prompt,
    build_pcb_layout_prompt,
)
from prompts.builder import estimate_tokens
from providers import get_provider
from providers.types import ProviderResponse
from utils.config import AppConfig, load_config


@dataclass
class ChatSendResult:
    response: ProviderResponse
    built: BuiltPrompt


def collect_chat_context(
    project_path: Path,
    *,
    config: AppConfig | None = None,
    include_image: bool = False,
    retry_failed_urls: bool = False,
    force_refresh_urls: bool = False,
    verbose: bool = False,
) -> ProjectContext:
    """Collect project context for the chat panel."""
    return collect_stretch_context(
        project_path,
        config=config,
        include_image=include_image,
        retry_failed_urls=retry_failed_urls,
        force_refresh_urls=force_refresh_urls,
        verbose=verbose,
    )


def build_chat_prompt(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include_image: bool = False,
    include: ContextIncludeFlags | None = None,
    template: str = "general_review",
) -> BuiltPrompt:
    """Build the chat prompt for a named audit template."""
    builders = {
        "general_review": build_general_review_prompt,
        "pcb_layout_audit": build_pcb_layout_prompt,
        "isolation_clearance_audit": build_isolation_clearance_prompt,
        "netlist_crosscheck": build_netlist_crosscheck_prompt,
        "netlist_gap_fill": build_netlist_gap_fill_prompt,
    }
    builder = builders.get(template, build_general_review_prompt)
    if template == "general_review":
        return builder(
            ctx,
            question,
            functional_description=functional_description,
            include_image=include_image,
            include=include,
        )
    return builder(
        ctx,
        question,
        functional_description=functional_description,
        include=include,
    )


def prepare_followup_context(
    ctx: ProjectContext,
    project_path: Path | str,
    *,
    config: AppConfig | None = None,
    include_flags: ContextIncludeFlags | None = None,
    include_image: bool = False,
    auto_refresh: bool = True,
) -> tuple[ProjectContext, set[str], ContextCacheEntry | None]:
    """
    Detect dirty layers and optionally refresh them before a follow-up send.

    Returns updated context, set of layers that were dirty, and cache entry if valid.
    """
    flags = include_flags or ContextIncludeFlags()
    relevant = layers_for_flags(flags)
    dirty = detect_dirty_layers(project_path) & relevant
    updated = ctx
    if dirty and auto_refresh:
        updated = refresh_context_layers(
            ctx,
            project_path,
            dirty,
            config=config,
            include_image=include_image and "image" in dirty,
        )
    cache_entry = load_context_cache(project_path) if cache_matches_project(project_path) else None
    return updated, dirty, cache_entry


def build_followup_prompt(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    template: str = "general_review",
    project_path: Path | str | None = None,
    dirty_layers: set[str] | None = None,
    cache_entry: ContextCacheEntry | None = None,
) -> BuiltPrompt:
    """Build a lighter follow-up prompt for multi-turn chat."""
    template_prompt = build_chat_prompt(
        ctx,
        question,
        functional_description=functional_description,
        include_image=False,
        template=template,
    )

    use_cache = (
        cache_entry is not None
        and (dirty_layers is None or not dirty_layers)
        and project_path is not None
        and cache_matches_project(project_path)
    )

    if use_cache and cache_entry is not None:
        snapshot = cache_entry.snapshot.format_summary()
        body = (
            "Follow-up question in an ongoing conversation. "
            "Full project context was provided in the first turn.\n\n"
            f"Cached project snapshot: {snapshot}\n\n"
        )
    else:
        snapshot_parts = [
            f"Project: {ctx.project_name}",
            f"Symbols: {len(ctx.symbols)}",
        ]
        if ctx.netlist_summary:
            line = ctx.netlist_summary.get("status_line")
            if line:
                snapshot_parts.append(str(line))
        snapshot = "; ".join(snapshot_parts)
        body = (
            "Follow-up question in an ongoing conversation. "
            "Full project context was provided in the first turn.\n\n"
            f"Current project snapshot: {snapshot}\n\n"
        )
        if dirty_layers:
            body += f"Updated layers since last turn: {', '.join(sorted(dirty_layers))}\n\n"

    if functional_description:
        body += f"Design intent: {functional_description}\n\n"
    body += f"Question: {question}"
    return BuiltPrompt(
        text=body,
        system=template_prompt.system,
        template=template,
        preview_summary=f"Follow-up — {ctx.project_name}",
        estimated_text_tokens=estimate_tokens(body),
        include_image=False,
        image_byte_size=0,
    )


def _resolve_config(
    config: AppConfig | None,
    api_key_override: str | None,
) -> AppConfig:
    cfg = config or load_config()
    if api_key_override and api_key_override.strip():
        return replace(cfg, anthropic_api_key=api_key_override.strip())
    return cfg


def send_chat_prompt(
    built: BuiltPrompt,
    ctx: ProjectContext,
    *,
    config: AppConfig | None = None,
    api_key_override: str | None = None,
    provider: Any | None = None,
    session: ChatSession | None = None,
) -> ChatSendResult:
    """Send a built prompt to the configured provider."""
    cfg = _resolve_config(config, api_key_override)
    resolved_provider = provider or get_provider(cfg)
    is_followup = session is not None and bool(session.turns)

    if is_followup:
        messages = session.to_api_messages()
        messages.append({"role": "user", "content": built.text})
        response = resolved_provider.send_messages(
            messages,
            system=built.system,
            config=cfg,
        )
    else:
        response = resolved_provider.send_message(
            built.text,
            system=built.system,
            image=ctx.schematic_image if built.include_image else None,
            config=cfg,
        )
    return ChatSendResult(response=response, built=built)
