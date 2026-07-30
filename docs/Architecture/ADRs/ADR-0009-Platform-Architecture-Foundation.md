# ADR-0009: Platform Architecture Foundation

[Home](../../../README.md) › [Project Index](../../../PROJECT_INDEX.md) › [Architecture](../README.md) › [ADRs](README.md) › ADR-0009

## Status

Accepted

## Date

2026-07-29

## Decision Owners

- Project maintainers

## Context

The KiCad AI Integration project has evolved from a KiCad plugin concept into an **AI-assisted Electrical Engineering Reasoning Platform** that uses KiCad as its primary engineering environment. Existing ADRs and ADPs (EKM, AERF, provider abstraction, prompt architecture) already define host-independent frameworks, but documentation and code organization remain KiCad-centric.

A wholesale repository reorganization would disrupt development continuity and invalidate cross-references in ratified ADRs. The project needs a formal platform layering model that:

- Positions KiCad as the first host integration, not the architectural boundary
- Distinguishes platform frameworks from host-specific adapters
- Introduces the Engineering Inference Engine (EIE) as the runtime orchestrator separate from AERF methodology
- Preserves existing ADRs 0001–0008 and ADPs 001–003, 008 as authoritative

Full architectural rationale is in [Platform Architecture](../Platform_Architecture.md), [ADP-009](../ADP-009-Host-Integration-Layer.md), and [ADP-010](../ADP-010-Engineering-Inference-Engine.md).

## Decision

Adopt a three-layer platform architecture:

1. **Platform** — product vision and cross-host contracts ([Platform Architecture](../Platform_Architecture.md))
2. **Frameworks** — EKM, AERF, EIE, Prompt Architecture, AI Provider Layer, Artifact Library, Engineering Knowledge Libraries
3. **Host Integrations** — KiCad AI Integration as the first reference implementation

Specific commitments:

- **AERP** as the formal umbrella acronym for the host-agnostic framework stack ([ADR-0010](ADR-0010-AERP-Platform-Umbrella-Acronym.md)). Supersedes the original “no platform acronym” commitment in this ADR.
- **KiCad remains the first host.** ADR-0001 and KiCad-specific docs stay authoritative for the reference host.
- **Overlay documentation, not relocation.** New platform docs sit above existing KiCad-centric architecture; ADRs/ADPs are not moved or rewritten.
- **`DesignSnapshot` protocol** defined in `src/platform_core/contracts.py`; `ProjectContext` is the KiCad implementation.
- **EIE at `src/inference/`** orchestrates inference; AERF stage definitions at `src/reasoning/`; EKM runtime at `src/ekm/`.
- **Physical `src/hosts/` reorganization deferred** until a second host integration is actively developed.

## Alternatives Considered

### Wholesale repository rename and directory restructure

- Advantages: Clean directory taxonomy immediately
- Disadvantages: Breaks git history continuity; invalidates hundreds of cross-references; disrupts active Phase 1 development
- Reason not selected: Preservation of history and continuity are higher priorities than a perfectly clean structure

### Introduce "EERP" as a formal platform acronym

- Advantages: Short label for the umbrella product
- Disadvantages: Adds terminology parallel to existing "platform" language and AERF; risks confusion with AERF
- Reason not selected: Descriptive prose and existing acronyms are sufficient

### Fold EIE into AERF as a single framework

- Advantages: Fewer named components
- Disadvantages: Conflates methodology (what to reason) with runtime orchestration (how to execute); blocks clean host independence
- Reason not selected: AERF is a framework within the platform; EIE is the execution engine

## Consequences

### Positive

- Clear platform/host boundary for future EDA tools, CLI, web, and laboratory integrations
- Existing ratified decisions remain valid without amendment
- Incremental code evolution via `src/platform/`, `src/inference/`, `src/reasoning/`, `src/ekm/`
- Developers can reason about import boundaries (platform must not import KiCad parsers/UI)

### Negative

- Temporary mismatch between logical layers and physical `src/` layout until second host
- KiCad-named paths (`kicad_ai/`, `ProjectContext`) persist for continuity

### Risks

- Platform logic leaking into `src/context/` KiCad parsers — mitigate with documented import rules and code review
- Premature `src/hosts/` extraction — mitigate by deferring until second host is real

## Implementation Notes

- Author `Platform_Architecture.md`, ADP-009, ADP-010; update indexes and cross-links
- Create `src/platform_core/contracts.py`, `src/inference/`, `src/reasoning/`, `src/ekm/` stubs
- Migrate chat workflow from `chat_supply.py` to `src/inference/chat.py`
- Reframe `KiCad_AI_Integration_Software_Architecture.md` as KiCad host implementation view

## References

- [Platform Architecture](../Platform_Architecture.md)
- [ADP-009: Host Integration Layer](../ADP-009-Host-Integration-Layer.md)
- [ADP-010: Engineering Inference Engine](../ADP-010-Engineering-Inference-Engine.md)
- [ADP-001: Engineering Knowledge Model Foundation](../ADP-001-Engineering-Knowledge-Model-Foundation.md)
- [ADP-008: AI Engineering Reasoning Framework](../ADP-008-AI-Engineering-Reasoning-Framework.md)
- [Project Overview](../../../PROJECT_OVERVIEW.md)

## Parent

- [Architecture Decision Records](README.md)
