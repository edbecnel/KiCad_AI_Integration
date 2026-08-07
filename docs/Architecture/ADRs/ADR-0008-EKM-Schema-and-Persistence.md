# ADR-0008: EKM Schema and Persistence

[Home](../../../README.md) › [Project Index](../../../PROJECT_INDEX.md) › [Architecture](../README.md) › [ADRs](README.md) › ADR-0008

## Status

Accepted

## Date

2026-07-29

## Decision Owners

- Project maintainers

## Context

[ADP-001](../ADP-001-Engineering-Knowledge-Model-Foundation.md) (v1.1) established the Engineering Knowledge Model (EKM) with a versioned minimum metamodel (§19) and deferred full JSON Schema, persistence naming, migration policy, and staleness detection to ADP-002.

[ADP-003](../ADP-003-Engineering-Notebook-User-Interface.md) and downstream ADPs require a stable schema contract before implementation. Without formal schema guardrails, EKM documents risk incompatibility across plugin versions and collaborative Git workflows.

Full architectural rationale is documented in [ADP-002: EKM Schema and Persistence](../ADP-002-EKM-Schema-and-Persistence.md) (v1.0).

## Decision

Adopt the **EKM schema and persistence contract** defined in ADP-002 and [`ekm_schema_v1.json`](../../Database/ekm_schema_v1.json):

- **Persistence:** `kicad_ai/engineering_knowledge.json` per project (UTF-8, pretty-printed JSON).
- **Schema version:** Semver string; first release `"1.0.0"`. Plugin rejects unknown **major** versions.
- **Structure:** Flat `sections[]` with optional `parent_id` and `order` for hierarchy; `fields[]` with six primitive types (`text`, `number`, `enum`, `reference`, `measurement`, `attachment`).
- **KiCad links:** Structured `KiCadLink` objects (`kind`, `ref`, optional `sheet_path`); not string tokens.
- **Attachments:** `ArtifactReference` objects (`artifact_id`) pointing to shared artifact library entries; no inline binary data.
- **Metadata:** Optional open `metadata` object on sections and fields; provenance semantics deferred to ADP-005.
- **Staleness:** Computed at read time against `ProjectContext`; not stored in EKM. Detection contract defined in ADP-002 §13.
- **Validation:** JSON Schema is source of truth; View Model validates before persistence (ADP-003 §11.1).
- **Git:** Commit `engineering_knowledge.json` to project VCS; reference-not-embed policy for binary content.
- **Empty documents:** Valid (`sections: []`); no plugin-shipped default engineering sections.

EKM load/save/validate runtime is implemented in `src/ekm/` with structural validation tests in `tests/ekm/`. Migration tooling and full CI schema gate remain future milestones.

## Alternatives Considered

### String token KiCad links (`ref:R1`, `net:+5V`)

- Advantages: Compact; matches informal notation in ADP-001 §19
- Disadvantages: Ambiguous parsing; poor extensibility for hierarchical schematics
- Reason not selected: Structured `KiCadLink` objects support `sheet_path` and explicit `kind`

### Nested `sections[]` instead of `parent_id`

- Advantages: Mirrors visual tree directly in JSON
- Disadvantages: Harder partial load, merge conflicts, and flat iteration
- Reason not selected: Flat list with `parent_id` supports ADP-003 lazy section loading

### Store staleness state in EKM

- Advantages: Persisted indicator survives offline review
- Disadvantages: Becomes stale itself; duplicates KiCad authority
- Reason not selected: Staleness computed from `ProjectContext` at read time

### Integer schema version

- Advantages: Simpler comparison
- Disadvantages: Less expressive for minor/patch migrations
- Reason not selected: Semver aligns with industry practice and ADP-002 migration policy

## Consequences

### Positive

- Stable contract for ADP-003 notebook implementation and ADP-004/005/006/007 downstream work
- JSON Schema enables automated validation and CI guardrails
- Aligns with existing `kicad_ai/project_manifest.json` persistence patterns
- Metadata extension point avoids ADP-005 schema redesign

### Negative

- View Model must implement schema validation and semver-aware load policy
- Structured KiCadLink is more verbose than string tokens

### Risks

- Git merge conflicts on large EKM files — mitigate with section-oriented structure and stable IDs
- Schema evolution requires governed version bumps — mitigate with semver major rejection policy
- `enum` value not in `options` requires View Model validation beyond JSON Schema — documented in ADP-002 §12.2

## Implementation Notes

- No code changes in this ADR; architecture and schema only
- **Implementation status:** See [ADP-002 §18](../ADP-002-EKM-Schema-and-Persistence.md#18-implementation) and Track B in [MASTER_TASK_LIST](../../../tasks/MASTER_TASK_LIST.md)
- Canonical schema: [`docs/Database/ekm_schema_v1.json`](../../Database/ekm_schema_v1.json)
- Example document: [ADP-002 Appendix A](../ADP-002-EKM-Schema-and-Persistence.md#appendix-a-example-engineering_knowledgejson)

## References

- [ADP-001: Engineering Knowledge Model Foundation](../ADP-001-Engineering-Knowledge-Model-Foundation.md)
- [ADP-002: EKM Schema and Persistence](../ADP-002-EKM-Schema-and-Persistence.md)
- [ADP-003: Engineering Notebook User Interface](../ADP-003-Engineering-Notebook-User-Interface.md)
- [ADR-0005: EKM Foundation](ADR-0005-EKM-Foundation.md)
- [ADR-0006: Engineering Notebook UI](ADR-0006-Engineering-Notebook-UI.md)
- [EKM JSON Schema v1](../../Database/ekm_schema_v1.json)
- [Database](../../Database/README.md)
- [Netlist Gap Fill](../../Specifications/Netlist_Gap_Fill.md)

## Parent

- [Architecture Decision Records](README.md)
