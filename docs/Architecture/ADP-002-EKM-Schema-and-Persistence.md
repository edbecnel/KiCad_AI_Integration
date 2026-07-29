# ADP-002: EKM Schema and Persistence

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Architecture](README.md) › ADP-002

**Status:** Accepted (v1.0 — revised per architecture review)

**Author:** Ed Becnel

**Project:** KiCad AI Integration Plugin

**Version:** 1.0

**Date:** 2026-07-29

**Ratified by:** [ADR-0008](ADRs/ADR-0008-EKM-Schema-and-Persistence.md)

**Builds on:** [ADP-001: Engineering Knowledge Model Foundation](ADP-001-Engineering-Knowledge-Model-Foundation.md) (v1.1)

**Downstream consumers:** [ADP-003](ADP-003-Engineering-Notebook-User-Interface.md), ADP-004, ADP-005, ADP-006, ADP-007, [ADP-008](ADP-008-AI-Engineering-Reasoning-Framework.md)

---

## 1. Purpose

This Architectural Design Proposal defines the **canonical JSON schema**, **persistence contract**, and **validation rules** for the Engineering Knowledge Model (EKM).

[ADP-001](ADP-001-Engineering-Knowledge-Model-Foundation.md) established the EKM as the authoritative representation of project engineering knowledge and committed to a versioned minimum metamodel (§19). This document formalizes that metamodel into a machine-readable schema and specifies how EKM documents are stored, versioned, and validated.

This proposal defines architecture and schema only. It does not define View Model implementation, notebook rendering, or AI write-back logic.

---

## 2. Background

The EKM is persisted as JSON under each project's `kicad_ai/` directory. Users interact with the [Engineering Notebook](ADP-003-Engineering-Notebook-User-Interface.md), not raw JSON. The View Model validates documents against this schema before persistence.

Without a formal schema:

- Implementers cannot validate EKM documents consistently.
- Downstream ADPs (notebook UI, NL conversion, provenance, prompt integration) lack a stable contract.
- Schema drift risks incompatibility between plugin versions and project files.

The canonical JSON Schema lives at [`docs/Database/ekm_schema_v1.json`](../Database/ekm_schema_v1.json).

---

## 3. Problem Statement

Engineering knowledge must be persisted reliably across plugin versions, Git workflows, and collaborative editing — while remaining domain-independent and extensible.

The schema must:

- Formalize ADP-001 §19 structural primitives.
- Support hierarchical notebook organization without hard-coded engineering pages.
- Reference KiCad design objects and shared artifact library entries without embedding binary data.
- Reserve extension points for provenance (ADP-005) without requiring a schema redesign.

---

## 4. Goals

The EKM schema and persistence layer shall:

- Provide a canonical JSON Schema for EKM documents.
- Define persistence location, file naming, and load/save lifecycle.
- Specify `schema_version` semantics and migration policy.
- Define primitive field type value shapes (`text`, `number`, `enum`, `reference`, `measurement`, `attachment`).
- Define KiCad link and artifact reference formats.
- Reserve a `metadata` extension object on sections and fields for ADP-005.
- Define a staleness **detection contract** for KiCad object links (computed at read time).
- Specify Git and merge policy for per-project EKM files.

---

## 5. Non-Goals

This proposal is not intended to:

- Define provenance semantics (`source`, `confidence`, `status`, revision history) — deferred to ADP-005.
- Define natural language → EKM conversion — deferred to ADP-004.
- Define notebook rendering or View Model implementation — deferred to ADP-003 implementation.
- Define AERF stage → EKM write-back mapping — deferred to ADP-007 (conceptual mapping exists in [ADP-008 §15](ADP-008-AI-Engineering-Reasoning-Framework.md)).
- Define simulation or measurement integration semantics — deferred to ADP-006.
- Ship plugin-shipped default engineering sections — empty documents are valid.
- Implement migration tooling or validation code — deferred to implementation.

---

## 6. Architectural Decisions

The following decisions were resolved during ADP-002 authoring:

| # | Topic | Decision |
|---|-------|----------|
| 1 | Staleness detection | ADP-002 defines link schema and a **detection contract** (validated against `ProjectContext` at read time). Staleness is **not stored** in the EKM. UI indicators (ADP-003) and prompt-time handling (ADP-007) consume detection results. |
| 2 | Metadata extension | ADP-002 defines an optional `metadata` object on sections and fields with **no required keys**. ADP-005 adds provenance key semantics without breaking v1 schema. |
| 3 | Section hierarchy | Flat `sections[]` with optional `parent_id` (references another section `id`) and `order` (integer sort key). Nested `sections[]` is **not** used in v1. |
| 4 | `schema_version` | Semver string. First release: `"1.0.0"`. Plugin **rejects** documents with unknown **major** version. Minor/patch migrations may be auto-applied by the plugin when implemented. |
| 5 | AERF section names | Names such as "Circuit Overview" and "Component Rationale" ([ADP-008 §15](ADP-008-AI-Engineering-Reasoning-Framework.md)) are **content conventions**, not required schema sections. An empty `sections: []` document is valid. |
| 6 | KiCad link format | Structured **KiCadLink** objects (not string tokens). Canonical shape defined in §7.4. |

---

## 7. Canonical Document Structure

An EKM document (`EKMDocument`) is the root object persisted to disk.

```
EKMDocument
  schema_version          # required; semver string, e.g. "1.0.0"
  project_path            # optional; absolute or project-relative path to .kicad_pro
  updated_at              # optional; ISO 8601 UTC timestamp of last save
  sections[]
    id                    # required; stable identifier (slug or UUID)
    title                 # required; human-readable section title
    parent_id             # optional; id of parent section for hierarchy
    order                 # optional; integer sort key among siblings
    fields[]
      id                  # required; stable identifier
      type                # required; primitive field type (see §8)
      label               # optional; field label (defaults to id in UI)
      value               # required; shape depends on type (see §8)
      options               # required when type is enum; allowed string values
      unit                  # optional when type is number; display unit hint
      links[]               # optional; additional KiCadLink references
      metadata              # optional; extension object (see §9)
    metadata              # optional; extension object (see §9)
```

### 7.1 Section identifiers

- `id` values must be unique within the document.
- `id` values should remain stable across edits so cross-references and AI write-back remain valid.
- Recommended format: lowercase slug (`constraints`, `component-rationale`) or UUID.

### 7.2 Section hierarchy

Sections form a tree via optional `parent_id`:

- Root sections omit `parent_id` or set it to `null`.
- Child sections set `parent_id` to the parent's `id`.
- `order` sorts siblings with the same `parent_id` (ascending; missing `order` sorts last).

The [Engineering Notebook](ADP-003-Engineering-Notebook-User-Interface.md) renders this as an expandable hierarchy.

### 7.3 Empty documents

A valid v1 document may contain `"sections": []`. The plugin does not inject default engineering sections. Content is populated by the user, AI (after approval), or import tooling.

### 7.4 KiCadLink object

KiCad object references use a structured object, not string tokens:

```json
{
  "kind": "component",
  "ref": "R1",
  "sheet_path": "flyback_driver.kicad_sch"
}
```

| Field | Required | Values |
|-------|----------|--------|
| `kind` | yes | `component`, `net`, `symbol`, `sheet` |
| `ref` | yes for `component`, `net`, `symbol` | Reference designator, net name, or symbol identifier |
| `sheet_path` | no | Schematic file path for hierarchical designs (see [Netlist_Gap_Fill](../Specifications/Netlist_Gap_Fill.md)) |

`reference` field values use a single KiCadLink object. Other field types may attach supplementary links via `links[]`.

### 7.5 ArtifactReference object

Attachment fields reference the shared artifact library (see [ADP-001 §10](ADP-001-Engineering-Knowledge-Model-Foundation.md#10-extensibility) and [Netlist_Gap_Fill](../Specifications/Netlist_Gap_Fill.md)):

```json
{
  "artifact_id": "ds-F0D3180-a1b2c3"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `artifact_id` | yes | Catalog entry ID from the shared artifact library |

Binary payloads (images, waveforms, simulation dumps) must **not** be embedded inline in the EKM document.

---

## 8. Primitive Field Type Specifications

The v1 schema supports six primitive field types. New primitives require a governed ADP and schema version bump.

### 8.1 `text`

Unstructured or markdown-capable text.

| Property | Type | Description |
|----------|------|-------------|
| `value` | string | Text content |

### 8.2 `number`

Numeric value with optional unit hint.

| Property | Type | Description |
|----------|------|-------------|
| `value` | number | Numeric value |
| `unit` | string (optional) | Display unit (e.g. `V`, `Ω`, `MHz`) |

Unit display in the notebook may also use `metadata` keys added by ADP-005; `unit` on the field is the v1 canonical hint.

### 8.3 `enum`

Selection from a fixed set of allowed values.

| Property | Type | Description |
|----------|------|-------------|
| `value` | string | Selected value (must be in `options`) |
| `options` | string[] | Allowed values (required on field definition) |

### 8.4 `reference`

Primary link to a KiCad design object.

| Property | Type | Description |
|----------|------|-------------|
| `value` | KiCadLink | Primary reference |

### 8.5 `measurement`

Bench or simulation measurement with conditions.

| Property | Type | Description |
|----------|------|-------------|
| `value` | object | `{ "value": number, "unit": string, "conditions": string (optional) }` |

Example:

```json
{
  "value": 3.3,
  "unit": "V",
  "conditions": "no load, T=25°C"
}
```

Full simulation integration semantics are deferred to ADP-006.

### 8.6 `attachment`

Reference to a shared artifact library entry.

| Property | Type | Description |
|----------|------|-------------|
| `value` | ArtifactReference | Artifact library pointer |

---

## 9. Metadata Extension Point

Sections and fields may include an optional `metadata` object.

**v1 rule:** `metadata` is an open object (additional properties allowed). No keys are required. No provenance semantics are defined in v1.

ADP-005 will define optional keys such as `source`, `confidence`, `status`, and `updated_at` without breaking v1 documents that omit them or use empty `metadata: {}`.

Implementers must tolerate unknown `metadata` keys (forward compatibility).

---

## 10. Persistence

### 10.1 File location and naming

| Property | Value |
|----------|-------|
| Directory | `<project_root>/kicad_ai/` |
| Filename | `engineering_knowledge.json` |
| Full path | `<project_root>/kicad_ai/engineering_knowledge.json` |

This aligns with existing per-project artifacts such as `project_manifest.json` ([`src/context/artifacts/manifest.py`](../../src/context/artifacts/manifest.py)).

### 10.2 Relationship to `project_manifest.json`

| File | Role |
|------|------|
| `project_manifest.json` | Per-project links from components/parts to **shared artifact library** entries (datasheets, SPICE libs) |
| `engineering_knowledge.json` | Per-project **authored engineering knowledge** (intent, rationale, decisions) |

These files are siblings under `kicad_ai/`. EKM `attachment` fields reference artifact library entries by `artifact_id`; they do not duplicate manifest link structure. A single artifact may be referenced from both the manifest (component datasheet) and the EKM (engineering note with attached waveform).

### 10.3 Load/save lifecycle

1. On project open, the plugin loads `engineering_knowledge.json` if present; otherwise initializes an empty document with `schema_version: "1.0.0"` and `sections: []`.
2. The View Model validates the document against the JSON Schema before accepting edits.
3. On save, the plugin writes atomically (write temp file, rename) with `updated_at` set to current UTC time.
4. Missing file is not an error — empty EKM is the default for new projects.

### 10.4 Encoding

- UTF-8
- Pretty-printed JSON with 2-space indent and trailing newline (consistent with `project_manifest.json`)

---

## 11. Schema Versioning and Migration

### 11.1 `schema_version` format

Semver string: `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking structural changes (plugin rejects unknown major version).
- **MINOR:** Backward-compatible additions (new optional fields, new primitive types with governed ADP).
- **PATCH:** Documentation or non-semantic schema annotation changes.

First release: `"1.0.0"`.

### 11.2 Migration policy

| Scenario | Behavior |
|----------|----------|
| Known version, current major | Load normally; apply minor/patch migrations if implemented |
| Unknown major version | Reject load; display error with required plugin version |
| Missing `schema_version` | Reject load (invalid document) |
| Empty `sections` | Valid |

Migration tooling implementation is deferred. This ADP defines the policy; implementers add migration functions per version increment.

---

## 12. Validation

### 12.1 JSON Schema as source of truth

The canonical schema is [`docs/Database/ekm_schema_v1.json`](../Database/ekm_schema_v1.json).

Validation occurs in the View Model layer before persistence ([ADP-003 §11.1](ADP-003-Engineering-Notebook-User-Interface.md#111-edit-and-validation-pathway)):

**Notebook UI → View Model (validate against JSON Schema) → EKM → persist**

### 12.2 Validation rules beyond JSON Schema

The View Model may enforce additional rules at runtime:

- `enum` values must be members of `options`.
- `parent_id` must reference an existing section `id` (no cycles).
- `reference` and `links[]` KiCadLink objects must have valid `kind`/`ref` combinations.
- Staleness detection (§13) produces warnings, not validation failures.

---

## 13. Staleness Model for KiCad Links

KiCad design objects may change after EKM links are authored (component renamed, net removed). Per [ADP-001 §16](ADP-001-Engineering-Knowledge-Model-Foundation.md#16-authority-boundaries), EKM links are **references**, not copies.

### 13.1 Detection contract

Staleness is **computed at read time** by comparing KiCadLink objects against the current `ProjectContext` snapshot. Staleness state is **not persisted** in the EKM document.

| Staleness | Condition |
|-----------|-----------|
| `valid` | Referenced object exists in current `ProjectContext` |
| `missing` | Referenced object not found (renamed, deleted, or wrong sheet) |
| `unchecked` | `ProjectContext` not available (headless mode, project not loaded) |

### 13.2 Consumers

| Consumer | Behavior |
|----------|----------|
| View Model | Exposes staleness status per link for UI and prompt assembly |
| Engineering Notebook (ADP-003) | May display staleness indicator on `reference` fields and `links[]` |
| Prompt integration (ADP-007) | May omit or flag stale links in prompt context |

Full UI behavior for staleness indicators is deferred to ADP-003 implementation.

---

## 14. Git and Merge Policy

### 14.1 Version control

- **Commit** `kicad_ai/engineering_knowledge.json` to project VCS (same policy as `project_manifest.json`).
- Do **not** commit shared artifact library binaries in the EKM file — attachments use `artifact_id` references only.

### 14.2 Merge conflicts

JSON merge conflicts are expected on collaborative projects. Mitigation strategies:

- Keep documents section-oriented so conflicts localize to edited sections.
- Use stable section and field `id` values so merges can be reconciled semantically in future tooling.
- Avoid embedding large blobs that inflate diff noise (reference-not-embed policy).

Optimistic concurrency (ETag, revision counters) is deferred to implementation.

---

## 15. Authority Boundaries

Restated from [ADP-001 §16](ADP-001-Engineering-Knowledge-Model-Foundation.md#16-authority-boundaries) for schema context:

| Domain | Authoritative source | In EKM schema |
|--------|---------------------|---------------|
| Electrical connectivity | KiCad schematic / netlist | Links only (`KiCadLink`) |
| Extracted design facts | `ProjectContext` | Not stored in EKM |
| Engineering intent, rationale, assumptions, curated decisions | EKM | `sections` and `fields` |
| Datasheets, SPICE libs, simulation exports | Artifact library | `attachment` via `artifact_id` |
| Chat transcript | Conversation Manager | Not stored in EKM |

---

## 16. Relationship to Other ADPs

| ADP | Relationship |
|-----|--------------|
| [ADP-001](ADP-001-Engineering-Knowledge-Model-Foundation.md) | Foundation; §19 minimum metamodel formalized here |
| [ADP-003](ADP-003-Engineering-Notebook-User-Interface.md) | Notebook renders and edits EKM documents conforming to this schema |
| [ADP-008](ADP-008-AI-Engineering-Reasoning-Framework.md) | AERF write-back targets EKM sections by convention (§6 decision 5); full mapping in ADP-007 |
| ADP-004 | NL capture produces EKM documents validated against this schema |
| ADP-005 | Adds `metadata` key semantics without v1 schema breakage |
| ADP-006 | Extends `measurement` semantics and simulation artifact references |
| ADP-007 | EKM summarization, prompt assembly, staleness handling at prompt time |

---

## 17. Acceptance Criteria

This proposal is considered complete when:

- A canonical JSON Schema exists at `docs/Database/ekm_schema_v1.json`.
- All six ADP-001 §19 primitives are specified with value shapes.
- Persistence path `kicad_ai/engineering_knowledge.json` is defined.
- `schema_version` semantics and migration policy are defined.
- KiCadLink and ArtifactReference formats are defined.
- Metadata extension point is reserved for ADP-005.
- Staleness detection contract is defined (computed, not stored).
- Git policy is stated.
- Authority boundaries are restated for schema context.

---

## 18. Implementation

Implementation is intentionally deferred.

| Component | Assigned to |
|-----------|-------------|
| View Model load/save/validate | ADP-003 implementation |
| Migration functions per version | Implementation milestone |
| JSON Schema CI validation tests | Implementation milestone |
| Staleness detection against `ProjectContext` | ADP-003 / ADP-007 implementation |

---

## 19. Decision

**Accepted (v1.0)**

The EKM schema and persistence contract defined in this ADP and [`ekm_schema_v1.json`](../Database/ekm_schema_v1.json) become the canonical specification for Engineering Knowledge Model documents.

Ratified as [ADR-0008: EKM Schema and Persistence](ADRs/ADR-0008-EKM-Schema-and-Persistence.md).

---

## Appendix A: Example `engineering_knowledge.json`

```json
{
  "schema_version": "1.0.0",
  "project_path": "/projects/flyback_driver/flyback_driver.kicad_pro",
  "updated_at": "2026-07-29T10:00:00Z",
  "sections": [
    {
      "id": "design-intent",
      "title": "Design Intent",
      "order": 0,
      "fields": [
        {
          "id": "summary",
          "type": "text",
          "label": "Summary",
          "value": "Isolated 12V flyback converter, 5W output."
        }
      ],
      "metadata": {}
    },
    {
      "id": "constraints",
      "title": "Constraints",
      "order": 1,
      "fields": [
        {
          "id": "max-input-voltage",
          "type": "number",
          "label": "Maximum input voltage",
          "value": 24,
          "unit": "V"
        }
      ]
    },
    {
      "id": "component-rationale",
      "title": "Component Rationale",
      "parent_id": null,
      "order": 2,
      "fields": [
        {
          "id": "u3-selection",
          "type": "text",
          "label": "U3 selection rationale",
          "value": "FOD3180 chosen for optocoupler CTR and package.",
          "links": [
            {
              "kind": "component",
              "ref": "U3",
              "sheet_path": "flyback_driver.kicad_sch"
            }
          ]
        },
        {
          "id": "u3-datasheet",
          "type": "attachment",
          "label": "U3 datasheet",
          "value": {
            "artifact_id": "ds-F0D3180-a1b2c3"
          }
        }
      ]
    }
  ]
}
```

---

## Appendix B: Deferred to Other ADPs

| Topic | Owner |
|-------|-------|
| Provenance `metadata` key semantics | ADP-005 |
| Natural language → EKM conversion | ADP-004 |
| Simulation/measurement field extensions | ADP-006 |
| AERF stage → EKM write-back mapping | ADP-007 |
| EKM summarization and token management | ADP-007 |
| Conflict resolution, undo/redo | ADP-004 / implementation |
| Optimistic concurrency control | Implementation |

---

## Related Documents

- [ADP-001: Engineering Knowledge Model Foundation](ADP-001-Engineering-Knowledge-Model-Foundation.md)
- [ADP-003: Engineering Notebook User Interface](ADP-003-Engineering-Notebook-User-Interface.md)
- [ADP-008: AI Engineering Reasoning Framework](ADP-008-AI-Engineering-Reasoning-Framework.md)
- [ADR-0005: EKM Foundation](ADRs/ADR-0005-EKM-Foundation.md)
- [ADR-0008: EKM Schema and Persistence](ADRs/ADR-0008-EKM-Schema-and-Persistence.md)
- [EKM JSON Schema v1](../Database/ekm_schema_v1.json)
- [Database](../Database/README.md)
- [Netlist Gap Fill](../Specifications/Netlist_Gap_Fill.md)

## Parent

- [Architecture](README.md)
