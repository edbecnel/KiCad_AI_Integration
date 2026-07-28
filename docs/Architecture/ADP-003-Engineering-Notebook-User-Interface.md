# ADP-003: Engineering Notebook User Interface

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Architecture](README.md) › ADP-003

**Status:** Accepted (v1.0 — revised per architecture review)

**Author:** Ed Becnel

**Project:** KiCad AI Integration Plugin

**Version:** 1.0

**Date:** 2026-07-28

**Ratified by:** [ADR-0006](ADRs/ADR-0006-Engineering-Notebook-UI.md)

**Builds on:** [ADP-001: Engineering Knowledge Model Foundation](ADP-001-Engineering-Knowledge-Model-Foundation.md) (v1.1)

**Upstream dependency:** ADP-002 (EKM schema and persistence — proposed, not yet ratified; see [ADP-001 Appendix A](ADP-001-Engineering-Knowledge-Model-Foundation.md#appendix-a-deferred-decisions) and [`docs/Database/`](../Database/README.md)). The minimum metamodel from ADP-001 §19 is sufficient for this architectural definition.

---

## 1. Purpose

This Architectural Design Proposal defines the Engineering Notebook, which serves as the primary human interface to the Engineering Knowledge Model (EKM).

The notebook is the user's workspace for viewing, organizing, and editing engineering knowledge associated with a KiCad project.

This proposal defines the user experience and rendering architecture. It does not define AI interaction or implementation details.

---

## 2. Background

[ADP-001](ADP-001-Engineering-Knowledge-Model-Foundation.md) established the Engineering Knowledge Model (EKM) as the canonical representation of engineering knowledge.

Users, however, should never interact directly with the underlying JSON representation.

Instead, they require an intuitive, document-oriented interface that presents engineering knowledge in a natural, organized, and editable form.

The Engineering Notebook fulfills this role.

---

## 3. Problem Statement

Raw structured data is not an effective interface for engineering design.

Engineers think in terms of:

- Objectives
- Constraints
- Assumptions
- Calculations
- Notes
- Measurements
- Decisions
- Simulations

The user interface must present these concepts in a way that feels like an engineering notebook rather than a database editor.

---

## 4. Goals

The Engineering Notebook shall:

- Present engineering knowledge in a human-readable form.
- Support structured and unstructured information.
- Allow incremental refinement of knowledge.
- Adapt dynamically to different engineering disciplines.
- Hide the underlying JSON representation.
- Support future AI-assisted editing.
- Support future simulation integration.

---

## 5. Non-Goals

The Engineering Notebook is not intended to:

- Replace the schematic editor.
- Replace Markdown documentation.
- Replace project notes.
- Become a generic document editor.
- Expose internal JSON structures during normal operation.
- Display extracted KiCad design facts as editable EKM content (see §17).

---

## 6. User Experience Philosophy

The Engineering Notebook should feel like an engineer's working notebook rather than a software configuration dialog.

Users should perceive the notebook as a living engineering document that evolves throughout the design process.

The interface should encourage capturing engineering knowledge as naturally as possible.

---

## 7. Dynamic Rendering

The notebook shall not contain hard-coded pages or forms.

Instead, it is dynamically generated from the Engineering Knowledge Model.

The rendering engine should interpret the EKM and construct the notebook at runtime.

As the EKM evolves, the notebook evolves automatically.

New engineering sections and domain content require **schema or EKM content changes only**, not plugin code changes — unless a new **primitive field type** is needed (see §10 and §11).

---

## 8. Notebook Organization

The notebook shall organize information hierarchically.

The following is an **example of EKM-authored structure**, not plugin defaults. The plugin does not ship hard-coded engineering pages. An empty project may start with a minimal metamodel-defined skeleton or no sections until populated by the user or AI.

Example:

```
Engineering Notebook
├── Project Overview
├── Objectives
├── Design Intent
├── Constraints
├── Assumptions
├── Components
├── Simulations
├── Measurements
├── AI Recommendations
├── Design Decisions
└── Open Questions
```

The actual organization is determined by the EKM rather than the plugin.

---

## 9. Rendering Components

The rendering engine should support generic presentation elements composed from EKM sections and fields.

Examples include:

- Headings (from section titles)
- Paragraphs
- Markdown
- Lists
- Tables
- Images (via artifact references)
- Attachments (via artifact references)
- Hyperlinks
- Notes
- Numeric values
- Unit-aware values
- Boolean values
- Enumerations

These rendering components are generic and independent of engineering discipline.

Headings, lists, and tables are **layout primitives** composed from sections and fields — they are not separate EKM field types.

### 9.1 Primitive Field Type Mapping

The dynamic notebook renderer understands **primitive field types** defined in [ADP-001 §19](ADP-001-Engineering-Knowledge-Model-Foundation.md#19-minimum-metamodel), not arbitrary JSON shapes. The mapping from EKM primitives to notebook presentation is:

| EKM primitive | Notebook presentation | Notes |
|---------------|-------------------------|-------|
| `text` | Paragraph, markdown block | Section `title` renders as heading |
| `number` | Numeric value editor | Unit display when metadata provides units |
| `enum` | Dropdown or radio group | Validation against allowed values |
| `reference` | Hyperlink to KiCad object | Staleness indicator deferred to ADP-002 or ADP-007 |
| `measurement` | Value + unit + conditions | Composite display for bench data |
| `attachment` | Image thumbnail or file link | Resolved via artifact library reference |

New primitive field types require a governed ADP. The renderer uses a **field-type registry** so new types can be added without rewriting the notebook shell.

### 9.2 Artifact Library References

Per [ADP-001 §10](ADP-001-Engineering-Knowledge-Model-Foundation.md#10-extensibility), large or binary payloads (images, waveforms, simulation dumps) must be stored as **references** to entries in the artifact library, not embedded inline in the EKM document.

The notebook displays thumbnails, previews, or links resolved from artifact references. It does not embed binary blobs in the editing surface.

---

## 10. Separation of Responsibilities

The Engineering Notebook architecture follows the layering established in [ADP-001 §6 and §8](ADP-001-Engineering-Knowledge-Model-Foundation.md#8-separation-of-responsibilities):

```
User
   │
   ▼
Engineering Notebook UI
   │
   ├──► Notebook Renderer (presentation widgets)
   │
   ▼
View Model
   │
   ▼
Engineering Knowledge Model (Canonical)
   │
   ▼
JSON Persistence
```

### Engineering Knowledge Model

Defines:

- Content
- Organization
- Relationships

Does not define visual presentation.

### View Model

Responsible for:

- Translating between the EKM and notebook presentation state.
- Validating engineering knowledge before persistence.
- Shielding the UI from JSON serialization and AI transport details.
- Edit commands and diff/merge hooks for future AI-proposed mutations.
- Cross-reference indexing at scale (graph cache for navigation, not in the renderer).

This layer elevates the existing headless `*_supply.py` orchestration pattern into a formal architectural boundary. It enables testable, UI-agnostic EKM logic.

### Notebook Renderer

Responsible for:

- Layout
- Navigation chrome (expand/collapse, scroll regions)
- Rendering primitive field types via the field-type registry
- Context-sensitive editing controls

Does not interpret engineering meaning. Does not validate or persist.

### Plugin

Responsible for:

- KiCad lifecycle integration (dockable panel shell).
- Orchestrating View Model, renderer, and persistence I/O.
- Managing version compatibility.
- Optional Advanced JSON View for debugging (not the primary editing surface).

Does not encode domain-specific engineering rules.

---

## 11. Editing Philosophy

The notebook should support direct editing.

Users edit engineering knowledge rather than editing data structures.

The notebook should provide context-sensitive editing controls appropriate to the type of information being displayed.

### 11.1 Edit and Validation Pathway

Edits follow a single pathway:

**Notebook UI → View Model (validate) → EKM → persist**

The View Model provides validation feedback for invalid values (for example, out-of-range enums, malformed references). Persistence occurs only after validation succeeds.

Notebook edits are local until persisted. AI-suggested mutations appear as proposals requiring explicit user approval before write-back — consistent with the existing "Approve & Send" pattern in the chat UI and [ADP-001 §14](ADP-001-Engineering-Knowledge-Model-Foundation.md#14-security-and-approval).

The following are intentionally deferred:

- Conflict resolution when user edits overlap AI-proposed changes ([ADP-004](ADP-001-Engineering-Knowledge-Model-Foundation.md#appendix-a-deferred-decisions))
- Undo/redo and edit transaction model (autosave vs. explicit save)
- Optimistic concurrency control

Future AI-assisted editing will build upon this editing model.

---

## 12. Navigation

The notebook should support:

- Expandable sections.
- Search.
- Filtering.
- Cross-references.
- Internal hyperlinks.
- Future backlinks.

For large projects, the View Model may expose **partial load by section ID** rather than requiring full-document load on open. Deep section trees should support collapse-by-default and lazy section loading.

Navigation should remain intuitive even for large engineering projects.

---

## 13. KiCad UI Shell Integration

The Engineering Notebook lives inside KiCad as a **dockable panel**, consistent with Phase 2 of the [Software Architecture](KiCad_AI_Integration_Software_Architecture.md).

### 13.1 Relationship to Chat

The notebook and the AI chat panel are **sibling surfaces**:

| Surface | Role |
|---------|------|
| Chat | Conversational input; raw multi-turn transcript |
| Engineering Notebook | Curated, structured engineering knowledge |

Per [ADP-001 §18](ADP-001-Engineering-Knowledge-Model-Foundation.md#18-relationship-to-conversation-manager), conversations are **input**; the EKM is the **distilled output** after user approval. The chat UI does not replace the notebook, and the notebook does not replace chat.

### 13.2 Cross-Navigation

EKM `reference` fields may link to KiCad design objects (reference designators, nets, symbols). Selecting a reference in the notebook may navigate to or highlight the corresponding object in KiCad. Full cross-navigation behavior is deferred to a future ADP.

### 13.3 Advanced JSON View

An optional Advanced JSON View may expose the raw EKM document for debugging or development. This view is outside the Notebook Renderer's normal editing mode and is not the primary editing surface ([ADP-001 §12](ADP-001-Engineering-Knowledge-Model-Foundation.md#12-json-persistence)).

---

## 14. Provenance Extension Points

Provenance (source, confidence, status, revision history) is deferred to [ADP-005](ADP-001-Engineering-Knowledge-Model-Foundation.md#appendix-a-deferred-decisions).

Rendering components must tolerate optional `metadata` on sections and fields without requiring ADP-005 to redesign the renderer. For example, the renderer should reserve space for future status badges or source icons even when metadata is empty.

---

## 15. Future Extensibility

The notebook architecture should allow future support for:

- Rich media.
- Embedded simulation results.
- Waveforms.
- Charts.
- Images.
- Measurement records.
- AI conversations.
- External references.
- Version comparisons.

These capabilities should require no redesign of the notebook architecture. Binary and large payloads continue to use artifact library references.

Adding new **section content** requires only EKM/schema changes. Adding new **primitive field types** requires a governed ADP and a registry entry in the renderer.

---

## 16. Acceptance Criteria

This proposal is considered complete when:

- The Engineering Notebook is defined as the primary user interface for the EKM.
- The notebook is dynamically generated.
- No hard-coded engineering pages exist.
- The notebook remains domain independent.
- The View Model, Notebook Renderer, and EKM have clearly separated responsibilities.
- Primitive field types are mapped to presentation components.
- KiCad shell integration and chat sibling relationship are defined.
- Artifact library references govern binary content display.
- Future AI capabilities can integrate without architectural changes.

---

## 17. Authority Boundaries

The notebook displays **authored** EKM knowledge — intent, rationale, assumptions, and curated decisions.

It does not display extracted KiCad design facts from `ProjectContext` as editable EKM content. Per [ADP-001 §16](ADP-001-Engineering-Knowledge-Model-Foundation.md#16-authority-boundaries):

| Domain | Authoritative source |
|--------|---------------------|
| Electrical connectivity | KiCad schematic / netlist |
| Extracted design facts | `ProjectContext` (derived, refreshable snapshot) |
| Engineering intent, rationale, assumptions, curated decisions | EKM |

Optional future panels that show extracted design snapshots alongside EKM content must be clearly labeled as read-only KiCad-derived context.

---

## 18. Implementation

Implementation is intentionally deferred.

Subsequent ADPs will define:

- Natural language capture ([ADP-004](ADP-001-Engineering-Knowledge-Model-Foundation.md#appendix-a-deferred-decisions)).
- Dynamic renderer implementation details.
- AI integration.
- Provenance visualization ([ADP-005](ADP-001-Engineering-Knowledge-Model-Foundation.md#appendix-a-deferred-decisions)).

Full EKM JSON Schema, persistence file naming, and migration tooling are defined in **ADP-002** (schema and persistence). ADP-003 may proceed architecturally against the minimum metamodel in ADP-001 §19; implementation should coordinate with ADP-002.

---

## 19. Decision

**Accepted (v1.0)**

The Engineering Notebook becomes the primary user-facing representation of the Engineering Knowledge Model, providing a dynamic, extensible, and domain-independent environment for capturing and managing engineering knowledge.

Ratified as [ADR-0006: Engineering Notebook UI](ADRs/ADR-0006-Engineering-Notebook-UI.md).

---

## Related Documents

- [ADP-001: Engineering Knowledge Model Foundation](ADP-001-Engineering-Knowledge-Model-Foundation.md)
- [ADR-0005: EKM Foundation](ADRs/ADR-0005-EKM-Foundation.md)
- [ADR-0006: Engineering Notebook UI](ADRs/ADR-0006-Engineering-Notebook-UI.md)
- [Software Architecture](KiCad_AI_Integration_Software_Architecture.md)
- [Prompt Architecture](Prompt_Architecture.md)
- [Security](../AI/Security.md)
- [Database](../Database/README.md)

## Parent

- [Architecture](README.md)
