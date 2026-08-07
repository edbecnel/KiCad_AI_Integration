# ADR-0007: AI Engineering Reasoning Framework Foundation

[Home](../../../README.md) › [Project Index](../../../PROJECT_INDEX.md) › [Architecture](../README.md) › [ADRs](README.md) › ADR-0007

## Status

Accepted

## Date

2026-07-28

## Decision Owners

- Project maintainers

## Context

The KiCad AI Integration project currently sends collected schematic context to an LLM via single-shot prompts (for example, `general_review`) or two-stage SUBCKT workflows (`facts` → `synthesis`). These patterns lack a generalized, explainable engineering reasoning process that mirrors how experienced electrical engineers analyze unfamiliar circuits.

Layered engineering documentation developed during power-electronics analysis revealed a reusable eight-stage reasoning progression: identification → operation → energy flow → physical principles → component roles → operating modes → system behavior → engineering analysis.

The project needs a first-class architectural component that defines this staged reasoning process, supports circuit-family-specific knowledge overlays, and feeds curated conclusions into the EKM — without embedding domain logic in plugin code.

Full architectural rationale and boundaries are documented in [ADP-008: AI Engineering Reasoning Framework](../ADP-008-AI-Engineering-Reasoning-Framework.md) (v1.0).

## Decision

Adopt the **AI Engineering Reasoning Framework (AERF)** as a foundational architectural pillar alongside the EKM:

- **Stages:** Eight canonical reasoning stages (0–7) with stable `stage_id`, overridable titles per circuit family, and sequential accumulated context
- **Authority:** `ProjectContext` owns extracted KiCad facts; Circuit Family KB owns reusable reference knowledge; AERF stage outputs are transient reasoning artifacts; EKM owns curated conclusions after user approval
- **Knowledge base:** Circuit family content lives in `docs/Engineering_Knowledge/Circuit_Families/` — documentation, not plugin code
- **Simulation:** Engineering understanding precedes simulation; simulation validates and refines prior stages, never substitutes for staged reasoning
- **Coexistence:** `general_review` remains valid for ad-hoc questions; AERF is the structured path for deep circuit analysis
- **Approval:** Cloud transmission per stage (or batch) and EKM write-back require explicit user approval

Phase 1 implementation complete: `src/reasoning/` stage registry and KB loader, circuit family classifier (`src/reasoning/classifier.py`), AERF orchestration (`src/inference/aerf.py`), per-stage prompts and EKM write-back ([ADP-007](../ADP-007-AERF-Prompt-Integration.md)), and `--ui-aerf` UI. Simulation closed loop ([ADP-006](../ADP-006-Simulation-Abstraction.md)) remains open.

## Alternatives Considered

### Single-shot LLM prompt on full schematic context

- Advantages: Simple implementation; matches current `general_review` pattern
- Disadvantages: Opaque reasoning; no reusable ontology; poor explainability; conflates facts with interpretation
- Reason not selected: Does not emulate structured engineering analysis; insufficient for project differentiation

### Embed circuit-family domain logic in plugin code

- Advantages: Fast runtime lookup; no external KB loading
- Disadvantages: Violates EKM domain independence (ADP-001 §9); requires plugin changes for every new family
- Reason not selected: KB content must live in documentation, not code

### Replace AERF with EKM sections alone

- Advantages: Single persistence model
- Disadvantages: EKM stores curated conclusions, not the reasoning process; no reference ontology for circuit families
- Reason not selected: AERF (process) and EKM (persistence) serve different roles

## Consequences

### Positive

- Explainable, transparent engineering reasoning distinguishable from generic AI schematic tools
- Reusable circuit-family ontology shared across projects
- Clear foundation for staged prompt templates, orchestrator, and simulation integration
- Aligns with existing SUBCKT two-stage precedent and Approve & Send pattern
- Partial stage runs support quick triage without full eight-stage analysis

### Negative

- Additional architectural layer to implement and maintain
- Multi-stage orchestration increases token cost and latency for full analyses
- Circuit Family KB requires ongoing documentation investment

### Risks

- Stage output schema drift without ADP-007 guardrails — mitigate with versioned schemas in Stage Index
- KB content staleness — mitigate with governance review per EDF lifecycle
- Users may expect immediate full analysis — mitigate with partial runs and clear UI mode selection

## Implementation Notes

- No code changes in this ADR; architecture only
- **Implementation status:** Tracks B–C complete; Blocking Oscillator KB in `docs/Engineering_Knowledge/Circuit_Families/Blocking_Oscillator/`; orchestrator in `src/reasoning/` and `src/inference/aerf.py`
- EDF domain scaffold: `docs/Engineering_Knowledge/`

## References

- [ADP-008: AI Engineering Reasoning Framework](../ADP-008-AI-Engineering-Reasoning-Framework.md)
- [ADP-001: Engineering Knowledge Model Foundation](../ADP-001-Engineering-Knowledge-Model-Foundation.md)
- [ADR-0005: EKM Foundation](ADR-0005-EKM-Foundation.md)
- [Prompt Architecture](../Prompt_Architecture.md)
- [Engineering Knowledge](../../Engineering_Knowledge/README.md)
- [Master Task List](../../../tasks/MASTER_TASK_LIST.md)

## Parent

- [Architecture Decision Records](README.md)
