"""Prompt template for AI datasheet URL discovery (Phase 1 — no live web search)."""

from __future__ import annotations

import json
from typing import Any

DATASHEET_DISCOVERY_SYSTEM = """You help locate official datasheet PDF URLs for electronic components.

Rules:
- Respond with JSON only: {{"urls": ["https://...", ...]}}
- Suggest at most {max_urls} HTTPS URLs, ordered best-first.
- Prefer direct manufacturer PDF links ending in .pdf on the manufacturer domain.
- Authorized distributor direct PDF links are acceptable only when no manufacturer PDF is known.
- Never suggest HTML product pages, login walls, or non-HTTPS links.
- Use the part number and symbol context; do not invent URLs that are unlikely to exist.
- If you cannot suggest any plausible PDF URL, return {{"urls": []}}."""


def build_datasheet_discovery_prompt(
    symbol_context: dict[str, Any],
    *,
    max_urls: int = 3,
) -> tuple[str, str]:
    """Return (user_prompt, system_prompt) for URL discovery."""
    system = DATASHEET_DISCOVERY_SYSTEM.format(max_urls=max_urls)
    user = (
        "Find official datasheet PDF URLs for this schematic symbol:\n\n"
        f"{json.dumps(symbol_context, indent=2)}\n\n"
        'Return JSON only: {"urls": ["https://..."]}'
    )
    return user, system
