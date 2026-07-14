# AI Provider Interface

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Architecture](README.md) › AI Provider Interface

> **Status:** Draft
> **Owner:** Project maintainers
> **Applies To:** KiCad AI Integration provider layer
> **Authoritative:** No

## Purpose

Define the abstract contract between the Prompt Builder and external LLM providers. Aligned with [ADR-0002: Provider Abstraction Layer](ADRs/ADR-0002-Provider-Abstraction-Layer.md).

## Abstract Interface

_To be detailed during Phase 1 implementation._

```python
send_message(prompt, config) -> response
```

## Configuration Schema

Planned configuration fields:

- API key source — environment variable `ANTHROPIC_API_KEY` for Phase 1
- Provider selection — enum for future multi-provider support
- Model identifier — e.g. `claude-3-5-sonnet-20241022`
- Timeout and retry policy

## Response Model

Planned response fields:

- Parsed text content from provider `content[]` blocks
- Token usage metadata — input and output counts
- Error classification for UI display

## Error Handling

Planned error categories:

- Authentication failure
- Rate limits
- Timeouts
- Malformed responses

## Provider Enum

Phase 1: Claude Sonnet 3.5 only.

Planned future providers: OpenAI, Gemini, Groq, Ollama, DeepSeek.

## Related Documents

- [ADR-0002: Provider Abstraction Layer](ADRs/ADR-0002-Provider-Abstraction-Layer.md)
- [Software Architecture](KiCad_AI_Integration_Software_Architecture.md)
- [Master Task List](../../tasks/MASTER_TASK_LIST.md) § 1.4
- [Security](../AI/Security.md)

## Parent

- [Architecture](README.md)
