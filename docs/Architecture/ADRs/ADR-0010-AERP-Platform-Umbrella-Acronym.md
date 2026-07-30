# ADR-0010: AERP Platform Umbrella Acronym

[Home](../../../README.md) › [Project Index](../../../PROJECT_INDEX.md) › [Architecture](../README.md) › [ADRs](README.md) › ADR-0010

## Status

Accepted

## Date

2026-07-31

## Decision Owners

- Project maintainers

## Context

[ADR-0009](ADR-0009-Platform-Architecture-Foundation.md) established a three-layer model (Platform / Frameworks / Host Integrations) and declined a formal platform acronym, citing risk of confusion with **AERF** and sufficiency of descriptive prose.

In practice, engineers need a **distinctive collective name** for the host-agnostic framework stack (EKM, AERF, EIE, Prompt Architecture, AI Provider Layer, Artifact Library, Engineering Knowledge Libraries, and related `src/` packages). Generic terms such as “the platform” are inadequate in conversation with colleagues who lack project context.

The long-form name — **AI-assisted Electrical Engineering Reasoning Platform** — remains correct for charters and formal documentation but is too long for daily engineering speech.

## Decision

Adopt **AERP** as the formal umbrella acronym:

**AERP** — **A**I-assisted **E**ngineering **R**easoning **P**latform

**AERP** denotes the **host-agnostic framework stack** — all reusable reasoning, knowledge, prompt, and provider capabilities that do not depend on KiCad, wxPython, or `pcbnew`.

### Scope of AERP

AERP **includes** (non-exhaustive):

- EKM, AERF, EIE
- Prompt Architecture and AI Provider Layer
- Artifact Library and Engineering Knowledge Libraries
- `DesignSnapshot` and other `platform_core` contracts
- Platform `src/` packages: `ekm/`, `reasoning/`, `inference/`, `prompts/`, `providers/`, `platform_core/`, `context/artifacts/`

AERP **excludes**:

- Host integrations (KiCad context collectors, UI shell, write-back parsers)
- KiCad AI Integration as a product name (that is the **first host** embedding AERP)

### AERP vs AERF (mandatory distinction)

| Term | Scope |
|------|--------|
| **AERP** | Umbrella — the full host-agnostic framework stack |
| **AERF** | One framework **within** AERP — staged reasoning methodology (stages 0–7) and circuit-family KB overlays |

**AERF is not a synonym for AERP.** Say “AERP stack” or “AERP frameworks” when referring to the collective; say “AERF stage 3” when referring to staged reasoning only.

### Long-form names

| Context | Use |
|---------|-----|
| Formal charters, ADPs, external papers | **AI-assisted Electrical Engineering Reasoning Platform** (unchanged) |
| Daily engineering speech, issues, PRs | **AERP** |
| Descriptive prose in architecture docs | **AERP** or **platform frameworks** (interchangeable when linked to this ADR) |

The AERP expansion intentionally compresses “Electrical Engineering” to “Engineering” for speakability. The longer form remains authoritative where domain precision matters.

## Alternatives Considered

### Retain ADR-0009 — no platform acronym

- Advantages: No new terminology
- Disadvantages: Engineers default to meaningless “platform” in conversation; no distinctive handle for outsiders
- Reason not selected: Communication gap outweighs collision risk when hierarchy is documented

### EERP (Electrical Engineering Reasoning Platform)

- Advantages: Closer to long-form name
- Disadvantages: Visually and phonetically closer to AERF; ERP collision with enterprise software
- Reason not selected: AERP provides clearer separation from AERF

### SEER, SCORE, or other novel coinages

- Advantages: Highly distinctive
- Disadvantages: No continuity with existing “AI-assisted … Reasoning Platform” language
- Reason not selected: AERP maps directly to established product vocabulary

## Consequences

### Positive

- Distinctive umbrella term for meetings, documentation, and onboarding
- Clear hierarchy: AERP ⊃ {EKM, AERF, EIE, …}
- KiCad host work can be described as “AERP embedded in KiCad”

### Negative

- One-time documentation sweep to replace ambiguous “platform” where AERP is meant
- Discipline required to avoid AERP/AERF conflation

### Supersedes

Partially supersedes [ADR-0009](ADR-0009-Platform-Architecture-Foundation.md) commitment: *“No new platform acronym.”* All other ADR-0009 decisions remain in force.

## Implementation Notes

- Update [Glossary and Acronyms](../../Reference/Glossary.md) — AERP as primary umbrella entry
- Update [Platform Architecture](../Platform_Architecture.md) — three-layer diagram and terminology
- Link from [PROJECT_INDEX](../../../PROJECT_INDEX.md) and root [README](../../../README.md)

## References

- [ADR-0009: Platform Architecture Foundation](ADR-0009-Platform-Architecture-Foundation.md)
- [Platform Architecture](../Platform_Architecture.md)
- [Glossary and Acronyms](../../Reference/Glossary.md)

## Parent

- [Architecture Decision Records](README.md)
