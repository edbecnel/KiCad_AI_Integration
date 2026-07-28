# ADR-0005: Engineering Knowledge Model Foundation

[Home](../../../README.md) › [Project Index](../../../PROJECT_INDEX.md) › [Architecture](../README.md) › [ADRs](README.md) › ADR-0005

## Status

Accepted

## Date

2026-07-28

## Decision Owners

- Project maintainers

## Context

KiCad schematics capture electrical connectivity but not engineering rationale — design intent, assumptions, constraints, measurements, simulation results, and curated decisions. AI-assisted analysis lacks this context when it is trapped in notebooks, email, or conversation.

The project needs a canonical, persistent, domain-independent model for engineering knowledge that complements (not replaces) KiCad extraction (`ProjectContext`) and session chat (Conversation Manager).

Full architectural rationale and boundaries are documented in [ADP-001: Engineering Knowledge Model Foundation](../ADP-001-Engineering-Knowledge-Model-Foundation.md) (v1.1).

## Decision

Adopt the **Engineering Knowledge Model (EKM)** as the canonical representation of project engineering knowledge:

- **Layering:** User → Engineering Notebook UI → View Model → EKM → JSON persistence → AI / plugin / tools
- **Authority:** EKM owns authored knowledge (intent, rationale, assumptions, curated decisions). KiCad owns connectivity. `ProjectContext` owns extracted design facts. Conversation Manager owns raw chat transcripts.
- **Persistence:** JSON under per-project `kicad_ai/`, with required `schema_version`. JSON is persistence only; users edit the notebook, not raw JSON.
- **Domain independence:** Plugin provides domain-agnostic primitives and KiCad linking; domain content is EKM/AI-populated.
- **Minimum metamodel:** Versioned document with sections, typed fields, stable IDs, optional links, and metadata extension points (full schema deferred to ADP-002).
- **Security:** EKM cloud transmission and AI write-back require explicit user approval.

Implementation is deferred. Subsequent ADPs define schema, UI, NL conversion, provenance, simulation integration, and prompt integration per [ADP-001 Appendix A](../ADP-001-Engineering-Knowledge-Model-Foundation.md#appendix-a-deferred-decisions).

## Alternatives Considered

### Extend ProjectContext with persistent fields

- Advantages: Reuses existing extraction model
- Disadvantages: Conflates derived KiCad facts with authored knowledge; refreshes would overwrite user intent
- Reason not selected: Different lifecycles and authority boundaries

### Store engineering knowledge only in chat history

- Advantages: No new persistence model
- Disadvantages: Unstructured, session-bound, poor prompt reuse, no curated project memory
- Reason not selected: Conflicts with Phase 3 project memory goals

### Replace schematic with knowledge graph

- Advantages: Unified model
- Disadvantages: Out of scope; KiCad remains connectivity authority
- Reason not selected: Explicit non-goal in ADP-001

## Consequences

### Positive

- Clear foundation for Engineering Notebook, AI collaboration, simulation, and measurement ADPs
- Separates extracted facts from authored knowledge
- Aligns with existing JSON persistence and headless supply patterns
- Domain extensibility without plugin changes for new section content

### Negative

- New architectural layer to implement and maintain
- Dual-model prompt assembly (ProjectContext + EKM) adds complexity

### Risks

- Schema drift without ADP-002 guardrails — mitigate with minimum metamodel and JSON Schema validation
- EKM/schematic divergence — mitigate with reference linking and future staleness detection
- JSON file growth and Git merge conflicts — mitigate with reference-not-embed policy and future history strategy

## Implementation Notes

- No code changes in this ADR; architecture only
- Ephemeral `functional_description` in chat migrates to EKM over time
- Suggested persistence path: `kicad_ai/engineering_knowledge.json` (non-binding until ADP-002)
- Schema home: [`docs/Database/`](../../Database/README.md)

## References

- [ADP-001: Engineering Knowledge Model Foundation](../ADP-001-Engineering-Knowledge-Model-Foundation.md)
- [Software Architecture](../KiCad_AI_Integration_Software_Architecture.md)
- [Prompt Architecture](../Prompt_Architecture.md)
- [ADR-0003: Stateless Phase 1 Context Model](ADR-0003-Stateless-Phase-1-Context-Model.md)
- [Security](../../AI/Security.md)
- [Master Task List](../../../tasks/MASTER_TASK_LIST.md)

## Parent

- [Architecture Decision Records](README.md)
