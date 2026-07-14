# ADR-0003: Stateless Phase 1 Context Model

[Home](../../../README.md) › [Project Index](../../../PROJECT_INDEX.md) › [Architecture](../README.md) › [ADRs](README.md) › ADR-0003

## Status

Accepted

## Date

2026-07-14

## Decision Owners

- Project maintainers

## Context

KiCad AI Integration evolves from a Phase 1 Python script MVP to a Phase 2 native plugin with dockable chat and conversation history. The software architecture defines both a stateless one-shot workflow and a future Conversation Manager.

The team must decide what context and conversation state Phase 1 carries to avoid scope creep while preserving a path to multi-turn chat.

## Decision

**Phase 1** uses a **stateless, one-shot request model**:

- Each user action collects fresh project context, builds a prompt, calls the provider once, and displays the response
- No persistent chat history across requests
- No Conversation Manager in Phase 1

**Phase 2 and later** introduce the **Conversation Manager** with:

- Multi-turn chat history within a session
- Prior conversation turns attached to subsequent API requests
- Incremental context refresh between turns

## Alternatives Considered

### Full conversational UI in Phase 1

- Advantages: Better user experience from first release
- Disadvantages: Significantly larger Phase 1 scope; wxPython chat UI complexity
- Reason not selected: Phase 1 goal is proving context extraction and provider integration

### Permanent stateless model

- Advantages: Simplest architecture
- Disadvantages: Poor engineering workflow for iterative design discussions
- Reason not selected: Phase 2 plugin with dockable chat is a core project goal

## Consequences

### Positive

- Phase 1 MVP scope is bounded and achievable
- Clear architectural boundary between Phase 1 script and Phase 2 plugin
- Provider layer remains simple — no session state in Phase 1

### Negative

- Phase 1 users cannot continue a multi-turn conversation without re-sending context

### Risks

- Users expect chat persistence in Phase 1 — mitigate with clear UI messaging and Phase 2 roadmap

## Implementation Notes

- Phase 1 UI: single wxPython dialog with Send, not a chat log
- Conversation Manager deferred to `src/` session module in Phase 2
- See [Roadmap](../Roadmap.md) for phase summary

## References

- [Software Architecture](../KiCad_AI_Integration_Software_Architecture.md)
- [Master Task List](../../../tasks/MASTER_TASK_LIST.md) Phase 1 and Phase 2
- [ADR-0002: Provider Abstraction Layer](ADR-0002-Provider-Abstraction-Layer.md)

## Parent

- [Architecture Decision Records](README.md)
