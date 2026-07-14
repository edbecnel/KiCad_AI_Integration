# AI Provider Interface

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Architecture](README.md) › AI Provider Interface

> **Status:** Implemented (Phase 1.4)
> **Owner:** Project maintainers
> **Applies To:** KiCad AI Integration provider layer
> **Authoritative:** No

## Purpose

Define the abstract contract between the Prompt Builder and external LLM providers. Aligned with [ADR-0002: Provider Abstraction Layer](ADRs/ADR-0002-Provider-Abstraction-Layer.md).

## Abstract Interface

Implemented in `src/providers/base.py` and `src/providers/claude.py`:

```python
def send_message(
    prompt: str,
    *,
    system: str | None = None,
    image: bytes | None = None,
    image_media_type: str = "image/png",
    config: AppConfig | None = None,
) -> ProviderResponse:
    ...
```

Factory: `get_provider(config: AppConfig) -> BaseProvider` in `src/providers/factory.py`.

Phase 1 providers are **stateless** — the caller passes the full prompt on each call (ADR-0003).

## Configuration Schema

Loaded via `src/utils/config.py` (`~/kicad_ai_config.json` or `KICAD_AI_CONFIG`):

| Key | Env override | Default | Description |
|-----|--------------|---------|-------------|
| `anthropic_api_key` | `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `ai_provider` | `KICAD_AI_PROVIDER` | `claude` | Provider backend |
| `claude_model` | — | `claude-3-5-sonnet-20241022` | Messages API model ID |
| `provider_timeout_sec` | — | `120` | HTTP timeout (seconds) |
| `provider_max_tokens` | — | `4096` | Max output tokens per request |

## Response Model

`ProviderResponse` (`src/providers/types.py`):

| Field | Type | Description |
|-------|------|-------------|
| `text` | `str` | Concatenated text from all `content[]` blocks |
| `model` | `str` | Model ID from API response |
| `usage` | `TokenUsage` | `input_tokens`, `output_tokens` |
| `stop_reason` | `str \| None` | API stop reason when present |
| `raw` | `dict \| None` | Full API JSON (debugging) |

## Error Handling

`src/providers/errors.py`:

| Exception | When |
|-----------|------|
| `AuthError` | Missing API key or HTTP 401 |
| `RateLimitError` | HTTP 429 |
| `TimeoutError` | Socket/HTTP timeout |
| `MalformedResponseError` | Non-JSON body or empty text content |
| `ProviderError` | Other HTTP or transport failures |

## Multimodal

When `image` bytes are provided (e.g. `ProjectContext.schematic_image` PNG from schematic export), `ClaudeProvider` sends an Anthropic Messages API `content` array with `image` + `text` blocks (ADR-0004).

## Provider Enum

Phase 1: `ProviderKind.CLAUDE` only (`ai_provider: "claude"`).

Planned future providers: OpenAI, Gemini, Groq, Ollama, DeepSeek.

## Dev entry point

`scripts/run_ai_assistant.py --ask "question"` collects stretch context and calls the provider for local smoke tests. This bypasses the future Approve & Send UI — development only.

## Related Documents

- [ADR-0002: Provider Abstraction Layer](ADRs/ADR-0002-Provider-Abstraction-Layer.md)
- [Software Architecture](KiCad_AI_Integration_Software_Architecture.md)
- [Master Task List](../../tasks/MASTER_TASK_LIST.md) § 1.4
- [Security](../AI/Security.md)

## Parent

- [Architecture](README.md)
