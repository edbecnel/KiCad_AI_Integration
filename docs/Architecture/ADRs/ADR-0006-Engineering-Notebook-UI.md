# ADR-0006: Engineering Notebook User Interface

[Home](../../../README.md) › [Project Index](../../../PROJECT_INDEX.md) › [Architecture](../README.md) › [ADRs](README.md) › ADR-0006

## Status

Accepted

## Date

2026-07-28

## Decision Owners

- Project maintainers

## Context

[ADP-001](../ADP-001-Engineering-Knowledge-Model-Foundation.md) (v1.1) established the Engineering Knowledge Model (EKM) as canonical project engineering knowledge and named the Engineering Notebook as the primary user interface. Users must never edit raw JSON during normal operation.

An architecture review of the initial notebook UI proposal identified gaps: missing View Model layer, no mapping from EKM primitive field types to presentation components, undefined KiCad shell integration, and a numbering conflict (notebook UI belongs in ADP-003 per ADP-001 Appendix A, not ADP-002 which is reserved for schema and persistence).

Full architectural rationale is documented in [ADP-003: Engineering Notebook User Interface](../ADP-003-Engineering-Notebook-User-Interface.md) (v1.0).

## Decision

Adopt the **Engineering Notebook** as the primary user-facing interface to the EKM:

- **Layering:** User → Engineering Notebook UI → View Model → EKM → JSON persistence. Notebook Renderer handles presentation widgets; View Model handles validation, presentation state, and edit commands.
- **Dynamic rendering:** No hard-coded engineering pages. Structure comes from EKM sections and fields constrained by the minimum metamodel.
- **Primitive field types:** Renderer uses a field-type registry mapping EKM primitives (`text`, `number`, `enum`, `reference`, `measurement`, `attachment`) to presentation components.
- **KiCad shell:** Notebook is a dockable panel; chat and notebook are sibling surfaces (conversation input vs. curated EKM output).
- **Binary content:** Images, waveforms, and simulation dumps render via artifact library references, not inline JSON.
- **Editing pathway:** UI → View Model (validate) → EKM → persist. AI mutations require explicit user approval.
- **Authority:** Notebook displays authored EKM knowledge only; extracted `ProjectContext` facts are not editable EKM content.

Phase 1 implementation complete: notebook renderer (`src/ui/notebook_renderer.py`), View Model integration (`src/ekm/view_model.py`), modal and non-modal notebook UI (`--ui-notebook`, `--ui-notebook-panel`). Dockable KiCad action plugin shell remains Phase 2 (widget ready in `src/ui/notebook_panel.py`). Conflict resolution, undo/redo, and provenance visualization remain deferred per ADP-001 Appendix A.

## Alternatives Considered

### Hard-coded engineering pages per discipline

- Advantages: Faster initial UI for electronics projects
- Disadvantages: Violates domain independence; requires plugin changes for new concepts
- Reason not selected: Conflicts with ADP-001 §9 and §11

### Direct JSON editing as primary surface

- Advantages: Simple to implement
- Disadvantages: Poor UX; exposes internal representation; error-prone
- Reason not selected: Explicit non-goal in ADP-001 §7 and §12

### Merge notebook into chat panel

- Advantages: Single UI surface
- Disadvantages: Conflates raw conversation with curated project knowledge; poor structure for long-lived engineering content
- Reason not selected: ADP-001 §18 authority boundary between Conversation Manager and EKM

## Consequences

### Positive

- Clear UI architecture for dynamic notebook rendering aligned with ADP-001
- View Model boundary enables headless testing and future AI write-back
- Field-type registry supports extensibility without shell redesign
- KiCad integration model defined (dockable panel, chat sibling)

### Negative

- Multiple layers (UI, renderer, View Model, EKM) to implement and maintain
- Implementation depends on ADP-002 schema work for full persistence

### Risks

- Renderer complexity for rich field types — mitigate with field-type registry and incremental primitive rollout
- Large notebook performance — mitigate with lazy section loading and View Model partial load
- UX confusion between chat and notebook — mitigate with clear sibling-surface roles

## Implementation Notes

- No code changes in this ADR; architecture only
- **Implementation status:** Track D complete except dockable KiCad plugin shell (Phase 2); see [MASTER_TASK_LIST](../../../tasks/MASTER_TASK_LIST.md) Track D and [ADP-003](../ADP-003-Engineering-Notebook-User-Interface.md) §18
- Advanced JSON View is debugging-only, outside normal notebook editing
- Staleness detection contract in [ADP-002 §13](../ADP-002-EKM-Schema-and-Persistence.md#13-staleness-model-for-kicad-links); UI indicators deferred

## References

- [ADP-001: Engineering Knowledge Model Foundation](../ADP-001-Engineering-Knowledge-Model-Foundation.md)
- [ADP-003: Engineering Notebook User Interface](../ADP-003-Engineering-Notebook-User-Interface.md)
- [ADR-0005: EKM Foundation](ADR-0005-EKM-Foundation.md)
- [Software Architecture](../KiCad_AI_Integration_Software_Architecture.md)
- [Prompt Architecture](../Prompt_Architecture.md)
- [Security](../../AI/Security.md)
- [Database](../../Database/README.md)

## Parent

- [Architecture Decision Records](README.md)
