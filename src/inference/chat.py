"""Ad-hoc chat inference workflow (general_review template)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from context.collector import collect_stretch_context
from context.model import ProjectContext
from prompts import BuiltPrompt, build_general_review_prompt
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
        retry_failed_urls=retry_failed_urls or force_refresh_urls,
        verbose=verbose,
    )


def build_chat_prompt(
    ctx: ProjectContext,
    question: str,
    *,
    functional_description: str | None = None,
    include_image: bool = False,
) -> BuiltPrompt:
    """Build the general review prompt for chat."""
    return build_general_review_prompt(
        ctx,
        question,
        functional_description=functional_description,
        include_image=include_image,
    )


def send_chat_prompt(
    built: BuiltPrompt,
    ctx: ProjectContext,
    *,
    config: AppConfig | None = None,
    api_key_override: str | None = None,
) -> ChatSendResult:
    """Send a built prompt to the configured provider."""
    cfg = config or load_config()
    if api_key_override and api_key_override.strip():
        cfg = AppConfig(
            artifact_library_path=cfg.artifact_library_path,
            datasheet_search_paths=cfg.datasheet_search_paths,
            schematic_image_dpi=cfg.schematic_image_dpi,
            datasheet_url_fetch=cfg.datasheet_url_fetch,
            url_fetch_timeout_sec=cfg.url_fetch_timeout_sec,
            url_fetch_read_timeout_sec=cfg.url_fetch_read_timeout_sec,
            url_fetch_warmup=cfg.url_fetch_warmup,
            kicad_cli=cfg.kicad_cli,
            anthropic_api_key=api_key_override.strip(),
            ai_provider=cfg.ai_provider,
            claude_model=cfg.claude_model,
            provider_timeout_sec=cfg.provider_timeout_sec,
            provider_read_timeout_sec=cfg.provider_read_timeout_sec,
            provider_max_tokens=cfg.provider_max_tokens,
        )
    provider = get_provider(cfg)
    response = provider.send_message(
        built.text,
        system=built.system,
        image=ctx.schematic_image if built.include_image else None,
        config=cfg,
    )
    return ChatSendResult(response=response, built=built)
