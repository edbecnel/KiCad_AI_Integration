"""Application configuration loaded from environment and optional local file."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

DEFAULT_ARTIFACT_LIBRARY = Path.home() / "kicad_ai_library"
DEFAULT_SCHEMATIC_IMAGE_DPI = 600
DEFAULT_URL_FETCH_TIMEOUT_SEC = 10
DEFAULT_URL_FETCH_READ_TIMEOUT_SEC = 60
DEFAULT_URL_FETCH_WARMUP = True
DEFAULT_CONFIG_FILENAME = "kicad_ai_config.json"
DEFAULT_AI_PROVIDER = "claude"
DEFAULT_CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
DEFAULT_PROVIDER_TIMEOUT_SEC = 120
DEFAULT_PROVIDER_MAX_TOKENS = 4096

DatasheetUrlFetchPolicy = Literal["if_missing", "always", "never"]
DEFAULT_DATASHEET_URL_FETCH: DatasheetUrlFetchPolicy = "if_missing"
AiProviderKind = Literal["claude"]


@dataclass
class AppConfig:
    """Runtime configuration for KiCad AI Integration."""

    artifact_library_path: Path = field(default_factory=lambda: DEFAULT_ARTIFACT_LIBRARY)
    datasheet_search_paths: list[Path] = field(default_factory=list)
    schematic_image_dpi: int = DEFAULT_SCHEMATIC_IMAGE_DPI
    datasheet_url_fetch: DatasheetUrlFetchPolicy = DEFAULT_DATASHEET_URL_FETCH
    url_fetch_timeout_sec: int = DEFAULT_URL_FETCH_TIMEOUT_SEC
    url_fetch_read_timeout_sec: int = DEFAULT_URL_FETCH_READ_TIMEOUT_SEC
    url_fetch_warmup: bool = DEFAULT_URL_FETCH_WARMUP
    kicad_cli: str | None = None
    anthropic_api_key: str | None = None
    ai_provider: AiProviderKind = DEFAULT_AI_PROVIDER
    claude_model: str = DEFAULT_CLAUDE_MODEL
    provider_timeout_sec: int = DEFAULT_PROVIDER_TIMEOUT_SEC
    provider_max_tokens: int = DEFAULT_PROVIDER_MAX_TOKENS

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppConfig:
        paths = data.get("datasheet_search_paths") or []
        return cls(
            artifact_library_path=Path(
                data.get("artifact_library_path", DEFAULT_ARTIFACT_LIBRARY)
            ).expanduser(),
            datasheet_search_paths=[Path(p).expanduser() for p in paths],
            schematic_image_dpi=int(
                data.get("schematic_image_dpi", DEFAULT_SCHEMATIC_IMAGE_DPI)
            ),
            datasheet_url_fetch=_parse_datasheet_url_fetch(data),
            url_fetch_timeout_sec=int(
                data.get("url_fetch_timeout_sec", DEFAULT_URL_FETCH_TIMEOUT_SEC)
            ),
            url_fetch_read_timeout_sec=int(
                data.get(
                    "url_fetch_read_timeout_sec",
                    DEFAULT_URL_FETCH_READ_TIMEOUT_SEC,
                )
            ),
            url_fetch_warmup=bool(
                data.get("url_fetch_warmup", DEFAULT_URL_FETCH_WARMUP)
            ),
            kicad_cli=data.get("kicad_cli") or os.environ.get("KICAD_CLI"),
            anthropic_api_key=data.get("anthropic_api_key")
            or os.environ.get("ANTHROPIC_API_KEY"),
            ai_provider=_parse_ai_provider(data),
            claude_model=str(data.get("claude_model", DEFAULT_CLAUDE_MODEL)),
            provider_timeout_sec=int(
                data.get("provider_timeout_sec", DEFAULT_PROVIDER_TIMEOUT_SEC)
            ),
            provider_max_tokens=int(
                data.get("provider_max_tokens", DEFAULT_PROVIDER_MAX_TOKENS)
            ),
        )


def _parse_ai_provider(data: dict[str, Any]) -> AiProviderKind:
    provider = str(data.get("ai_provider", DEFAULT_AI_PROVIDER)).lower()
    if provider == "claude":
        return "claude"
    return DEFAULT_AI_PROVIDER


def _parse_datasheet_url_fetch(data: dict[str, Any]) -> DatasheetUrlFetchPolicy:
    """Parse datasheet URL fetch policy with backward compat for fetch_datasheet_urls bool."""
    if "datasheet_url_fetch" in data:
        policy = str(data["datasheet_url_fetch"]).lower()
        if policy in ("if_missing", "always", "never"):
            return policy  # type: ignore[return-value]
    if "fetch_datasheet_urls" in data and not data.get("datasheet_url_fetch"):
        return "never" if not data["fetch_datasheet_urls"] else "if_missing"
    return DEFAULT_DATASHEET_URL_FETCH


def _load_config_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_config(config_path: Path | None = None) -> AppConfig:
    """Load config from optional JSON file merged with environment variables."""
    candidates: list[Path] = []
    if config_path is not None:
        candidates.append(config_path.expanduser())
    else:
        env_path = os.environ.get("KICAD_AI_CONFIG")
        if env_path:
            candidates.append(Path(env_path).expanduser())
        candidates.append(Path.home() / DEFAULT_CONFIG_FILENAME)

    merged: dict[str, Any] = {}
    for candidate in candidates:
        if candidate.is_file():
            merged.update(_load_config_file(candidate))
            break

    if os.environ.get("KICAD_CLI"):
        merged["kicad_cli"] = os.environ["KICAD_CLI"]
    if os.environ.get("ANTHROPIC_API_KEY"):
        merged["anthropic_api_key"] = os.environ["ANTHROPIC_API_KEY"]
    if os.environ.get("KICAD_AI_LIBRARY"):
        merged["artifact_library_path"] = os.environ["KICAD_AI_LIBRARY"]
    env_fetch = os.environ.get("KICAD_AI_DATASHEET_URL_FETCH")
    if env_fetch:
        merged["datasheet_url_fetch"] = env_fetch.lower()
    elif os.environ.get("KICAD_AI_FETCH_URLS") is not None:
        merged["fetch_datasheet_urls"] = os.environ["KICAD_AI_FETCH_URLS"].lower() in (
            "1",
            "true",
            "yes",
        )
    if os.environ.get("KICAD_AI_PROVIDER"):
        merged["ai_provider"] = os.environ["KICAD_AI_PROVIDER"].lower()

    return AppConfig.from_dict(merged)
