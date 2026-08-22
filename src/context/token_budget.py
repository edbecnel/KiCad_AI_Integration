"""Token budgeting helpers for prompt size estimation."""

from __future__ import annotations

from typing import Any

from context.model import ProjectContext

_CHARS_PER_TOKEN = 4
_LARGE_SYMBOL_THRESHOLD = 50
_WARN_TOKEN_THRESHOLD = 12_000


def estimate_tokens_from_text(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // _CHARS_PER_TOKEN)


def estimate_context_tokens(ctx: ProjectContext) -> dict[str, Any]:
    """Estimate prompt payload size before assembly."""
    json_text = ctx.to_json(include_image_bytes=False)
    text_tokens = estimate_tokens_from_text(json_text)
    image_tokens = 0
    if ctx.schematic_image:
        image_tokens = max(1, len(ctx.schematic_image) // 800)
    total = text_tokens + image_tokens
    return {
        "text_characters": len(json_text),
        "estimated_text_tokens": text_tokens,
        "estimated_image_tokens": image_tokens,
        "estimated_total_tokens": total,
        "symbol_count": len(ctx.symbols),
        "use_compact_symbols": len(ctx.symbols) > _LARGE_SYMBOL_THRESHOLD,
        "warn_large_payload": total >= _WARN_TOKEN_THRESHOLD,
    }
