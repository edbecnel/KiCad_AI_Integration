# ADR-0002: Provider Abstraction Layer

[Home](../../../README.md) › [Project Index](../../../PROJECT_INDEX.md) › [Architecture](../README.md) › [ADRs](README.md) › ADR-0002

## Status

Accepted

## Date

2026-07-14

## Decision Owners

- Project maintainers

## Context

KiCad AI Integration must communicate with external LLM providers starting with Anthropic Claude Sonnet 3.5. The project charter and software architecture require provider independence so future models and vendors can be added without rewriting the Context Collection Engine or Prompt Builder.

Phase 1 needs a concrete implementation; long-term needs a stable abstraction boundary.

## Decision

Implement an **AI Provider Layer** with an abstract interface:

```python
send_message(prompt, config) -> response
```

Phase 1 delivers a **Claude Sonnet 3.5** implementation using the Anthropic Messages API (`https://api.anthropic.com/v1/messages`, model `claude-3-5-sonnet-20241022` or current Sonnet 3.5 identifier).

The provider layer includes:

- A provider enum and configuration schema for future providers (OpenAI, Gemini, Ollama, etc.)
- Structured error handling for auth failure, rate limits, timeouts, and malformed responses
- Token usage metadata in responses for future cost display

## Alternatives Considered

### Direct Anthropic API calls throughout the codebase

- Advantages: Fastest Phase 1 implementation
- Disadvantages: Tight coupling; every future provider requires wide refactors
- Reason not selected: Conflicts with provider-independence goal in project charter

### Plugin-per-provider architecture from day one

- Advantages: Maximum extensibility
- Disadvantages: Over-engineering before any second provider is needed
- Reason not selected: Simple abstract interface plus enum is sufficient for Phase 1

## Consequences

### Positive

- Clean separation between KiCad context logic and cloud AI vendors
- Enables Phase 2 multi-provider profile switching
- Testable via mocked HTTP responses in unit tests

### Negative

- Small upfront design cost before first working provider

### Risks

- Abstraction too narrow for streaming or tool-use APIs — mitigate by revisiting in a future ADR when Phase 2 features require it

## Implementation Notes

- Code lives under `src/providers/`
- See [AI Provider Interface](../AI_Provider_Interface.md) for draft contract detail
- Related to [ADR-0003](ADR-0003-Stateless-Phase-1-Context-Model.md) — provider layer is stateless in Phase 1

## References

- [Software Architecture](../KiCad_AI_Integration_Software_Architecture.md)
- [Master Task List](../../../tasks/MASTER_TASK_LIST.md) § 1.4
- [ADR-0003: Stateless Phase 1 Context Model](ADR-0003-Stateless-Phase-1-Context-Model.md)

## Parent

- [Architecture Decision Records](README.md)
