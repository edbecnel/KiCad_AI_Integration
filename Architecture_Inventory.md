# Architecture Documentation Inventory

Inventory of all documentation under `docs/Architecture/`. Generated from existing files only; no recommendations or gap analysis.

---

# 1. Architecture Folder Tree

```
docs/Architecture/
├── README.md
├── Platform_Architecture.md
├── KiCad_AI_Integration_Software_Architecture.md
├── Prompt_Architecture.md
├── AI_Provider_Interface.md
├── Roadmap.md
├── ADP-001-Engineering-Knowledge-Model-Foundation.md
├── ADP-002-EKM-Schema-and-Persistence.md
├── ADP-003-Engineering-Notebook-User-Interface.md
├── ADP-006-Simulation-Abstraction.md
├── ADP-013-Routing-Abstraction.md
├── ADP-014-Firmware-Aware-Mixed-Domain-Simulation.md
├── ADP-007-AERF-Prompt-Integration.md
├── ADP-008-AI-Engineering-Reasoning-Framework.md
├── ADP-009-Host-Integration-Layer.md
├── ADP-010-Engineering-Inference-Engine.md
├── ADP-011-Assistant-Shell-UI.md
└── ADRs/
    ├── README.md
    ├── ADR-0001-KiCad-8-Minimum-Version.md
    ├── ADR-0002-Provider-Abstraction-Layer.md
    ├── ADR-0003-Stateless-Phase-1-Context-Model.md
    ├── ADR-0004-Optional-Multimodal-Schematic-Context.md
    ├── ADR-0005-EKM-Foundation.md
    ├── ADR-0006-Engineering-Notebook-UI.md
    ├── ADR-0007-AERF-Foundation.md
    ├── ADR-0008-EKM-Schema-and-Persistence.md
    ├── ADR-0009-Platform-Architecture-Foundation.md
    └── ADR-0010-AERP-Platform-Umbrella-Acronym.md
```

Note: A `.DS_Store` file exists in `docs/Architecture/` but is not part of the documentation set.

---

# 2. Document Inventory

## docs/Architecture/README.md

| Field | Value |
|-------|-------|
| **Filename** | `README.md` |
| **Relative path** | `docs/Architecture/README.md` |
| **Brief purpose** | Index and navigation hub for the Architecture documentation domain. Lists authoritative documents, ADRs, ADPs, and scope guidance for what belongs in this folder. |
| **Approximate size** | ~60 lines, ~2.8 KB |
| **Major headings/sections** | Purpose; Authoritative Documents; Architecture Decision Records; Architectural Design Proposals; What Belongs Here; Navigation; Maintenance |
| **Documents it references** | `../../README.md`, `../../PROJECT_INDEX.md`, `Platform_Architecture.md`, `KiCad_AI_Integration_Software_Architecture.md`, ADP-001 through ADP-010, `Prompt_Architecture.md`, `AI_Provider_Interface.md`, `Roadmap.md`, `ADRs/README.md`, `../../ARCHITECTURE_DECISIONS.md`, all ADR files |
| **Classification** | Canonical |
| **Layer** | Platform |

---

## docs/Architecture/Platform_Architecture.md

| Field | Value |
|-------|-------|
| **Filename** | `Platform_Architecture.md` |
| **Relative path** | `docs/Architecture/Platform_Architecture.md` |
| **Brief purpose** | Authoritative platform overview: three-layer model (Platform / Frameworks / Host Integrations), authority boundaries, source code logical layers, import rules, future host patterns. |
| **Approximate size** | ~180 lines |
| **Major headings/sections** | Purpose; Three-Layer Model; Platform Frameworks; AERF vs EIE; Authority Boundaries; Host Integration Layer; Source Code Logical Layers; Future Host Applications; Related Documents |
| **Documents it references** | ADR-0009, ADP-001, ADP-008, ADP-009, ADP-010, KiCad Software Architecture, Prompt Architecture, AI Provider Interface |
| **Classification** | Canonical |
| **Layer** | Platform |

---

## docs/Architecture/KiCad_AI_Integration_Software_Architecture.md

| Field | Value |
|-------|-------|
| **Filename** | `KiCad_AI_Integration_Software_Architecture.md` |
| **Relative path** | `docs/Architecture/KiCad_AI_Integration_Software_Architecture.md` |
| **Brief purpose** | KiCad host implementation view. Describes project goals, phased delivery (Phase 1–3), KiCad-specific software components, security principles, and KiCad host long-term vision. |
| **Approximate size** | ~270 lines |
| **Major headings/sections** | Parent; Overview; Project Goals; Phase 1–3; Major Software Components; Security; KiCad Host Long-Term Vision; Related Documents |
| **Documents it references** | `Platform_Architecture.md`, `ADP-008`, `ADP-009`, `ADP-010`, `ADRs/ADR-0004`, `../Specifications/Netlist_Gap_Fill.md`, `../../tasks/MASTER_TASK_LIST.md`, `../Developer_Handbook/README.md` |
| **Classification** | Draft |
| **Layer** | Host (KiCad) |

---

## docs/Architecture/Prompt_Architecture.md

| Field | Value |
|-------|-------|
| **Filename** | `Prompt_Architecture.md` |
| **Relative path** | `docs/Architecture/Prompt_Architecture.md` |
| **Brief purpose** | Defines how KiCad project context is assembled into structured prompts for AI providers. Covers template system, XML-style prompt sections, multimodal schematic context, netlist gap-fill templates, future AERF stage templates, and token budgeting. |
| **Approximate size** | ~148 lines, ~6.6 KB |
| **Major headings/sections** | Purpose; Template System; Structured Prompt Sections; Multimodal Context (When to include, Export pipeline, Dependencies, User approval); Netlist Gap-Fill Prompt Templates (Connectivity inference, SUBCKT / `.lib` generation); AERF Stage Prompt Templates; Token Budgeting; Related Documents; Parent |
| **Documents it references** | `../../README.md`, `../../PROJECT_INDEX.md`, `README.md`, `KiCad_AI_Integration_Software_Architecture.md`, `../Specifications/Netlist_Gap_Fill.md`, `../AI/Prompting_Guide.md`, `../Developer_Handbook/Guide-Programmatic_AI_Analysis.md`, `ADRs/ADR-0004-Optional-Multimodal-Schematic-Context.md`, `ADRs/ADR-0003-Stateless-Phase-1-Context-Model.md`, `ADP-008-AI-Engineering-Reasoning-Framework.md`, `../Engineering_Knowledge/AERF_Stage_Index.md`, `../Engineering_Knowledge/README.md`, `../AI/Cost_Optimization.md`, `../../tasks/MASTER_TASK_LIST.md` |
| **Classification** | Canonical |

---

## docs/Architecture/AI_Provider_Interface.md

| Field | Value |
|-------|-------|
| **Filename** | `AI_Provider_Interface.md` |
| **Relative path** | `docs/Architecture/AI_Provider_Interface.md` |
| **Brief purpose** | Defines the abstract contract between the Prompt Builder and external LLM providers. Documents the implemented Phase 1.4 interface, configuration schema, response model, error handling, multimodal support, and provider enum. |
| **Approximate size** | ~93 lines, ~3.2 KB |
| **Major headings/sections** | Purpose; Abstract Interface; Configuration Schema; Response Model; Error Handling; Multimodal; Provider Enum; Dev entry point; Related Documents; Parent |
| **Documents it references** | `../../README.md`, `../../PROJECT_INDEX.md`, `README.md`, `ADRs/ADR-0002-Provider-Abstraction-Layer.md`, `KiCad_AI_Integration_Software_Architecture.md`, `../../tasks/MASTER_TASK_LIST.md`, `../AI/Security.md` |
| **Classification** | Canonical |

---

## docs/Architecture/Roadmap.md

| Field | Value |
|-------|-------|
| **Filename** | `Roadmap.md` |
| **Relative path** | `docs/Architecture/Roadmap.md` |
| **Brief purpose** | High-level phase roadmap for KiCad AI Integration across Phase 1 (Python script MVP), Phase 2 (native plugin), and Phase 3 (advanced engineering assistant). Points to the Master Task List for detailed implementation tasks. |
| **Approximate size** | ~59 lines, ~1.9 KB |
| **Major headings/sections** | Purpose; Phase 1 — Python Script MVP; Phase 2 — Native KiCad Plugin; Phase 3 — Advanced Engineering Assistant; Related Documents; Parent |
| **Documents it references** | `../../README.md`, `../../PROJECT_INDEX.md`, `README.md`, `ADRs/ADR-0003-Stateless-Phase-1-Context-Model.md`, `KiCad_AI_Integration_Software_Architecture.md`, `ADP-008-AI-Engineering-Reasoning-Framework.md`, `../../tasks/MASTER_TASK_LIST.md`, `../../PROJECT_CHARTER.md` |
| **Classification** | Draft |

---

## docs/Architecture/ADP-001-Engineering-Knowledge-Model-Foundation.md

| Field | Value |
|-------|-------|
| **Filename** | `ADP-001-Engineering-Knowledge-Model-Foundation.md` |
| **Relative path** | `docs/Architecture/ADP-001-Engineering-Knowledge-Model-Foundation.md` |
| **Brief purpose** | Architectural Design Proposal defining the Engineering Knowledge Model (EKM) as the canonical representation of project engineering knowledge. Establishes layering, authority boundaries, minimum metamodel, domain independence, and deferred decisions. |
| **Approximate size** | ~511 lines, ~17.3 KB |
| **Major headings/sections** | 1. Purpose; 2. Background; 3. Problem Statement; 4. Goals; 5. Non-Goals; 6. Architecture; 7. Canonical Representation; 8. Separation of Responsibilities; 9. Domain Independence; 10. Extensibility; 11. Human-Readable Representation; 12. JSON Persistence; 13. Future Metadata; 14. Security and Approval; 15. Acceptance Criteria; 16. Authority Boundaries; 17. Relationship to ProjectContext; 18. Relationship to Conversation Manager; 19. Minimum Metamodel; 20. Implementation; 21. Decision; Appendix A: Deferred Decisions; Related Documents; Parent |
| **Documents it references** | `../../README.md`, `../../PROJECT_INDEX.md`, `README.md`, `ADP-008-AI-Engineering-Reasoning-Framework.md`, `../Engineering_Knowledge/README.md`, `ADRs/ADR-0005-EKM-Foundation.md`, `ADRs/ADR-0003-Stateless-Phase-1-Context-Model.md`, `ADRs/ADR-0006-Engineering-Notebook-UI.md`, `ADP-003-Engineering-Notebook-User-Interface.md`, `KiCad_AI_Integration_Software_Architecture.md`, `Prompt_Architecture.md`, `../AI/Security.md`, `../Database/README.md`, `../../tasks/MASTER_TASK_LIST.md`, `../../src/context/model.py`, `../../src/prompts/templates/general_review.py` |
| **Classification** | Architectural Design Proposal (ADP) |

---

## docs/Architecture/ADP-003-Engineering-Notebook-User-Interface.md

| Field | Value |
|-------|-------|
| **Filename** | `ADP-003-Engineering-Notebook-User-Interface.md` |
| **Relative path** | `docs/Architecture/ADP-003-Engineering-Notebook-User-Interface.md` |
| **Brief purpose** | Architectural Design Proposal defining the Engineering Notebook as the primary human interface to the EKM. Covers dynamic rendering, View Model separation, primitive field type mapping, KiCad shell integration, editing philosophy, and authority boundaries. |
| **Approximate size** | ~424 lines, ~15.2 KB |
| **Major headings/sections** | 1. Purpose; 2. Background; 3. Problem Statement; 4. Goals; 5. Non-Goals; 6. User Experience Philosophy; 7. Dynamic Rendering; 8. Notebook Organization; 9. Rendering Components (9.1 Primitive Field Type Mapping, 9.2 Artifact Library References); 10. Separation of Responsibilities; 11. Editing Philosophy (11.1 Edit and Validation Pathway); 12. Navigation; 13. KiCad UI Shell Integration (13.1 Relationship to Chat, 13.2 Cross-Navigation, 13.3 Advanced JSON View); 14. Provenance Extension Points; 15. Future Extensibility; 16. Acceptance Criteria; 17. Authority Boundaries; 18. Implementation; 19. Decision; Related Documents; Parent |
| **Documents it references** | `../../README.md`, `../../PROJECT_INDEX.md`, `README.md`, `ADP-001-Engineering-Knowledge-Model-Foundation.md`, `ADRs/ADR-0006-Engineering-Notebook-UI.md`, `ADRs/ADR-0005-EKM-Foundation.md`, `KiCad_AI_Integration_Software_Architecture.md`, `Prompt_Architecture.md`, `../AI/Security.md`, `../Database/README.md` |
| **Classification** | Architectural Design Proposal (ADP) |

---

## docs/Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md

| Field | Value |
|-------|-------|
| **Filename** | `ADP-008-AI-Engineering-Reasoning-Framework.md` |
| **Relative path** | `docs/Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md` |
| **Brief purpose** | Architectural Design Proposal defining the AI Engineering Reasoning Framework (AERF), an eight-stage engineering reasoning process between context collection and EKM population. Covers stage execution, internal engineering reasoning methodology, circuit family overlays, knowledge loading, simulation philosophy, and coexistence with `general_review`. |
| **Approximate size** | ~510 lines, ~20 KB |
| **Major headings/sections** | 1. Purpose; 2. Background; 3. Problem Statement; 4. Goals; 5. Non-Goals; 6. Architecture; 7. Authority Boundaries; 8. Canonical Reasoning Stages; 9. Stage Execution Model (Internal Engineering Reasoning Methodology, Scientific neutrality); 10. Circuit Family Overlay Model; 11. Circuit Family Recognition; 12. Knowledge Loading Contract; 13. Simulation Philosophy; 14. Relationship to Prompt Architecture; 15. Relationship to EKM; 16. Coexistence with `general_review`; 17. Domain Independence; 18. Security and Approval; 19. Implementation; 20. Decision; Appendix A: Per-Stage Determinations (Summary); Related Documents; Parent |
| **Documents it references** | `../../README.md`, `../../PROJECT_INDEX.md`, `README.md`, `ADP-001-Engineering-Knowledge-Model-Foundation.md`, `ADRs/ADR-0007-AERF-Foundation.md`, `ADRs/ADR-0005-EKM-Foundation.md`, `ADRs/ADR-0004-Optional-Multimodal-Schematic-Context.md`, `Prompt_Architecture.md`, `KiCad_AI_Integration_Software_Architecture.md`, `../Engineering_Knowledge/README.md`, `../Engineering_Knowledge/AERF_Stage_Index.md`, `../Engineering_Knowledge/Engineering_Reasoning_Methodology.md`, `../Engineering_Knowledge/Circuit_Families/README.md`, `../AI/Security.md`, `../../tasks/MASTER_TASK_LIST.md` |
| **Classification** | Architectural Design Proposal (ADP), v1.1 |

---

## docs/Engineering_Knowledge/Engineering_Reasoning_Methodology.md

| Field | Value |
|-------|-------|
| **Filename** | `Engineering_Reasoning_Methodology.md` |
| **Relative path** | `docs/Engineering_Knowledge/Engineering_Reasoning_Methodology.md` |
| **Brief purpose** | Defines the common engineering reasoning methodology used internally by every AERF stage: evidence collection, knowledge classification (10 types), evidence chains, scientific neutrality, integrity principle, contradictory evidence handling, and human review points. Not a software architecture document. |
| **Approximate size** | ~320 lines |
| **Major headings/sections** | 1. Purpose and Scope; 2. Relationship to AERF; 3. Reasoning Process; 4. Knowledge Classification Model; 5. Evidence Chains; 6. Scientific Neutrality Principle; 7. Respect for Design Intent; 8. Integrity Principle; 9. Contradictory Evidence; 10. Human Review Points; 11. Relationship to EKM Provenance; Related Documents; Parent |
| **Documents it references** | `../../README.md`, `../../PROJECT_INDEX.md`, `../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md`, `AERF_Stage_Index.md`, `../Architecture/ADRs/ADR-0007-AERF-Foundation.md`, `../Architecture/ADP-001-Engineering-Knowledge-Model-Foundation.md`, `README.md` |
| **Classification** | Engineering Knowledge methodology (referenced by ADP-008 v1.1) |

---

## docs/Architecture/ADRs/README.md

| Field | Value |
|-------|-------|
| **Filename** | `README.md` |
| **Relative path** | `docs/Architecture/ADRs/README.md` |
| **Brief purpose** | Index for the Architecture Decision Records directory. Provides a table of all ADRs with ID, decision title, status, and date. |
| **Approximate size** | ~27 lines, ~1.4 KB |
| **Major headings/sections** | Purpose; ADR Index; Navigation |
| **Documents it references** | `../../../README.md`, `../../../PROJECT_INDEX.md`, `../README.md`, `../../../ARCHITECTURE_DECISIONS.md`, all seven ADR files |
| **Classification** | Canonical |

---

## docs/Architecture/ADRs/ADR-0001-KiCad-8-Minimum-Version.md

| Field | Value |
|-------|-------|
| **Filename** | `ADR-0001-KiCad-8-Minimum-Version.md` |
| **Relative path** | `docs/Architecture/ADRs/ADR-0001-KiCad-8-Minimum-Version.md` |
| **Brief purpose** | Records the decision to target KiCad 8.0 or later as the minimum supported version for Python scripting, schematic APIs, and wxPython UI integration. |
| **Approximate size** | ~79 lines, ~2.4 KB |
| **Major headings/sections** | Status; Date; Decision Owners; Context; Decision; Alternatives Considered (KiCad 7.x support, KiCad 9+ only); Consequences (Positive, Negative, Risks); Implementation Notes; References; Parent |
| **Documents it references** | `../../../README.md`, `../../../PROJECT_INDEX.md`, `../README.md`, `README.md`, `../../Developer_Handbook/01_Development_Environment.md`, `../KiCad_AI_Integration_Software_Architecture.md`, `../../../tasks/MASTER_TASK_LIST.md` |
| **Classification** | Architecture Decision Record (ADR) |

---

## docs/Architecture/ADRs/ADR-0002-Provider-Abstraction-Layer.md

| Field | Value |
|-------|-------|
| **Filename** | `ADR-0002-Provider-Abstraction-Layer.md` |
| **Relative path** | `docs/Architecture/ADRs/ADR-0002-Provider-Abstraction-Layer.md` |
| **Brief purpose** | Records the decision to implement an AI Provider Layer with an abstract `send_message` interface, starting with Claude Sonnet 3.5, to enable future multi-provider support. |
| **Approximate size** | ~83 lines, ~2.8 KB |
| **Major headings/sections** | Status; Date; Decision Owners; Context; Decision; Alternatives Considered (Direct Anthropic API calls, Plugin-per-provider architecture); Consequences (Positive, Negative, Risks); Implementation Notes; References; Parent |
| **Documents it references** | `../../../README.md`, `../../../PROJECT_INDEX.md`, `../README.md`, `README.md`, `../KiCad_AI_Integration_Software_Architecture.md`, `../AI_Provider_Interface.md`, `ADR-0003-Stateless-Phase-1-Context-Model.md`, `../../../tasks/MASTER_TASK_LIST.md` |
| **Classification** | Architecture Decision Record (ADR) |

---

## docs/Architecture/ADRs/ADR-0003-Stateless-Phase-1-Context-Model.md

| Field | Value |
|-------|-------|
| **Filename** | `ADR-0003-Stateless-Phase-1-Context-Model.md` |
| **Relative path** | `docs/Architecture/ADRs/ADR-0003-Stateless-Phase-1-Context-Model.md` |
| **Brief purpose** | Records the decision that Phase 1 uses a stateless one-shot request model with no persistent chat history, deferring the Conversation Manager to Phase 2 and later. |
| **Approximate size** | ~81 lines, ~2.6 KB |
| **Major headings/sections** | Status; Date; Decision Owners; Context; Decision; Alternatives Considered (Full conversational UI in Phase 1, Permanent stateless model); Consequences (Positive, Negative, Risks); Implementation Notes; References; Parent |
| **Documents it references** | `../../../README.md`, `../../../PROJECT_INDEX.md`, `../README.md`, `README.md`, `../KiCad_AI_Integration_Software_Architecture.md`, `../Roadmap.md`, `ADR-0002-Provider-Abstraction-Layer.md`, `../../../tasks/MASTER_TASK_LIST.md` |
| **Classification** | Architecture Decision Record (ADR) |

---

## docs/Architecture/ADRs/ADR-0004-Optional-Multimodal-Schematic-Context.md

| Field | Value |
|-------|-------|
| **Filename** | `ADR-0004-Optional-Multimodal-Schematic-Context.md` |
| **Relative path** | `docs/Architecture/ADRs/ADR-0004-Optional-Multimodal-Schematic-Context.md` |
| **Brief purpose** | Records the decision to support optional multimodal schematic context via `kicad-cli` PDF export and `pdftoppm` rasterization at 600 DPI, with opt-in UI and user approval before cloud transmission. |
| **Approximate size** | ~120 lines, ~5.2 KB |
| **Major headings/sections** | Status; Date; Decision Owners; Context; Decision (Export pipeline, Opt-in, User approval, Graceful degradation, Export commands); Alternatives Considered (SVG export, 300 DPI, Always-on image, Screen capture, KiCad 9+ native PNG); Consequences (Positive, Negative, Risks); Implementation Notes; References; Parent |
| **Documents it references** | `../../../README.md`, `../../../PROJECT_INDEX.md`, `../README.md`, `README.md`, `ADR-0001-KiCad-8-Minimum-Version.md`, `ADR-0003-Stateless-Phase-1-Context-Model.md`, `../Prompt_Architecture.md`, `../KiCad_AI_Integration_Software_Architecture.md`, `../../AI/Security.md`, `../../Reference/AI_Tools_for_Advanced_Circuit_Analysis.md`, `../../../tasks/MASTER_TASK_LIST.md` |
| **Classification** | Architecture Decision Record (ADR) |

---

## docs/Architecture/ADRs/ADR-0005-EKM-Foundation.md

| Field | Value |
|-------|-------|
| **Filename** | `ADR-0005-EKM-Foundation.md` |
| **Relative path** | `docs/Architecture/ADRs/ADR-0005-EKM-Foundation.md` |
| **Brief purpose** | Records the decision to adopt the Engineering Knowledge Model (EKM) as the canonical representation of project engineering knowledge, with JSON persistence, domain-independent primitives, and explicit authority boundaries. |
| **Approximate size** | ~96 lines, ~4.5 KB |
| **Major headings/sections** | Status; Date; Decision Owners; Context; Decision; Alternatives Considered (Extend ProjectContext, Chat-only storage, Knowledge graph replacement); Consequences (Positive, Negative, Risks); Implementation Notes; References; Parent |
| **Documents it references** | `../../../README.md`, `../../../PROJECT_INDEX.md`, `../README.md`, `README.md`, `../ADP-001-Engineering-Knowledge-Model-Foundation.md`, `../KiCad_AI_Integration_Software_Architecture.md`, `../Prompt_Architecture.md`, `ADR-0003-Stateless-Phase-1-Context-Model.md`, `../../AI/Security.md`, `../../Database/README.md`, `../../../tasks/MASTER_TASK_LIST.md` |
| **Classification** | Architecture Decision Record (ADR) |

---

## docs/Architecture/ADRs/ADR-0006-Engineering-Notebook-UI.md

| Field | Value |
|-------|-------|
| **Filename** | `ADR-0006-Engineering-Notebook-UI.md` |
| **Relative path** | `docs/Architecture/ADRs/ADR-0006-Engineering-Notebook-UI.md` |
| **Brief purpose** | Records the decision to adopt the Engineering Notebook as the primary user-facing interface to the EKM, with dynamic rendering, View Model layering, primitive field type registry, and dockable KiCad panel integration. |
| **Approximate size** | ~98 lines, ~4.8 KB |
| **Major headings/sections** | Status; Date; Decision Owners; Context; Decision; Alternatives Considered (Hard-coded pages, Direct JSON editing, Merge notebook into chat); Consequences (Positive, Negative, Risks); Implementation Notes; References; Parent |
| **Documents it references** | `../../../README.md`, `../../../PROJECT_INDEX.md`, `../README.md`, `README.md`, `../ADP-001-Engineering-Knowledge-Model-Foundation.md`, `../ADP-003-Engineering-Notebook-User-Interface.md`, `ADR-0005-EKM-Foundation.md`, `../KiCad_AI_Integration_Software_Architecture.md`, `../Prompt_Architecture.md`, `../../AI/Security.md`, `../../Database/README.md` |
| **Classification** | Architecture Decision Record (ADR) |

---

## docs/Architecture/ADRs/ADR-0007-AERF-Foundation.md

| Field | Value |
|-------|-------|
| **Filename** | `ADR-0007-AERF-Foundation.md` |
| **Relative path** | `docs/Architecture/ADRs/ADR-0007-AERF-Foundation.md` |
| **Brief purpose** | Records the decision to adopt the AI Engineering Reasoning Framework (AERF) as a foundational architectural pillar with eight canonical reasoning stages, circuit family knowledge overlays, and curated EKM write-back after user approval. |
| **Approximate size** | ~100 lines, ~5.2 KB |
| **Major headings/sections** | Status; Date; Decision Owners; Context; Decision; Alternatives Considered (Single-shot prompt, Embedded domain logic, EKM-only model); Consequences (Positive, Negative, Risks); Implementation Notes; References; Parent |
| **Documents it references** | `../../../README.md`, `../../../PROJECT_INDEX.md`, `../README.md`, `README.md`, `../ADP-008-AI-Engineering-Reasoning-Framework.md`, `../ADP-001-Engineering-Knowledge-Model-Foundation.md`, `ADR-0005-EKM-Foundation.md`, `../Prompt_Architecture.md`, `../../Engineering_Knowledge/README.md`, `../../../tasks/MASTER_TASK_LIST.md` |
| **Classification** | Architecture Decision Record (ADR) |

---

# 3. Architecture Decision Records

## ADR-0001: KiCad 8+ Minimum Version

**Status:** Accepted (2026-07-14)

KiCad AI Integration targets KiCad 8.0 or later as the minimum supported version because the project depends on `pcbnew`, schematic access APIs, and wxPython within KiCad's embedded Python interpreter. KiCad 7.x was rejected due to API inconsistency; KiCad 9+ only was rejected as premature. The decision establishes a clear prerequisite for development environment documentation, integration testing, and Context Collection Engine API assumptions.

---

## ADR-0002: Provider Abstraction Layer

**Status:** Accepted (2026-07-14)

The project implements an AI Provider Layer with an abstract `send_message(prompt, config) -> response` interface, with Phase 1 delivering a Claude Sonnet 3.5 implementation via the Anthropic Messages API. The layer includes a provider enum, configuration schema, structured error handling, and token usage metadata. Direct API calls throughout the codebase and a plugin-per-provider architecture from day one were both rejected in favor of a simple abstraction sufficient for Phase 1 with a path to multi-provider support in Phase 2.

---

## ADR-0003: Stateless Phase 1 Context Model

**Status:** Accepted (2026-07-14)

Phase 1 uses a stateless one-shot request model where each user action collects fresh project context, builds a prompt, calls the provider once, and displays the response with no persistent chat history or Conversation Manager. Phase 2 and later introduce multi-turn chat with session history and incremental context refresh. Full conversational UI in Phase 1 was rejected due to scope; a permanent stateless model was rejected because dockable chat is a core Phase 2 goal.

---

## ADR-0004: Optional Multimodal Schematic Context

**Status:** Accepted (2026-07-14)

Phase 1 supports optional multimodal schematic context via an external export pipeline (`kicad-cli sch export pdf` followed by `pdftoppm` at 600 DPI default), not in-process `pcbnew` rasterization. Schematic images are opt-in via UI checkbox, require explicit user approval before cloud transmission, and degrade gracefully when tools are missing. Alternatives including SVG rasterization, 300 DPI default, always-on images, screen capture, and KiCad 9+ native PNG export were considered and rejected based on fidelity, cost, reproducibility, or version constraints.

---

## ADR-0005: Engineering Knowledge Model Foundation

**Status:** Accepted (2026-07-28)

The project adopts the Engineering Knowledge Model (EKM) as the canonical representation of project engineering knowledge. EKM runtime, schema validation, Notebook UI, and AERF write-back are implemented (Tracks B–D). NL conversion (ADP-004) and provenance (ADP-005) remain deferred per ADP-001 Appendix A. Analog simulation closed loop (ADP-006) is implemented; firmware-aware mixed-domain simulation (ADP-014) is proposed.

---

## ADR-0006: Engineering Notebook User Interface

**Status:** Accepted (2026-07-28)

The Engineering Notebook is adopted as the primary user-facing interface to the EKM. Phase 1 notebook UI is implemented (`--ui-notebook`); dockable KiCad plugin shell remains Phase 2.

---

## ADR-0007: AI Engineering Reasoning Framework Foundation

**Status:** Accepted (2026-07-28)

The project adopts AERF as a foundational pillar alongside the EKM. Orchestration, classifier, per-stage prompts (ADP-007), Blocking Oscillator KB, and EKM write-back are implemented. Analog simulation closed loop (ADP-006) is implemented; firmware-aware mixed-domain simulation (ADP-014) is proposed.

---

## ADR-0008: EKM Schema and Persistence

**Status:** Accepted (2026-07-29)

The project adopts the EKM schema and persistence contract: `kicad_ai/engineering_knowledge.json`, semver `schema_version` (first release 1.0.0), six primitive field types, structured KiCadLink and ArtifactReference objects, optional metadata extension point, staleness computed at read time, and JSON Schema validation via View Model. Nested sections[], string token links, and persisted staleness state were rejected. Implementation of load/save and migration tooling is deferred.

---

## ADR-0009: Platform Architecture Foundation

**Status:** Accepted (2026-07-29)

The project adopts a three-layer platform architecture (Platform / Frameworks / Host Integrations) with KiCad AI Integration as the first host reference implementation. Platform frameworks (EKM, AERF, EIE, prompts, providers) are host-independent. Overlay documentation is preferred over wholesale reorganization. `DesignSnapshot` protocol lives in `src/platform_core/contracts.py`; EIE at `src/inference/`. Physical `src/hosts/` reorganization is deferred until a second host is actively developed. Wholesale repo rename and introducing a new platform acronym were rejected.

---

# 4. Architectural Design Proposals

## ADP-001: Engineering Knowledge Model (EKM) Foundation

**Status:** Accepted (v1.1, 2026-07-28), ratified by ADR-0005

ADP-001 defines the Engineering Knowledge Model as canonical project engineering knowledge. Tracks B–D implemented EKM runtime, Notebook UI, AERF, and prompt/write-back integration (ADP-007). ADP-004 and ADP-005 remain deferred. ADP-006 analog closed loop is implemented; ADP-014 firmware-aware mixed-domain simulation is proposed.

---

## ADP-002: EKM Schema and Persistence

**Status:** Accepted (v1.0, 2026-07-29), ratified by ADR-0008, builds on ADP-001

ADP-002 formalizes the EKM minimum metamodel into a canonical JSON Schema (`docs/Database/ekm_schema_v1.json`), defines persistence at `kicad_ai/engineering_knowledge.json`, semver migration policy, KiCadLink and ArtifactReference formats, metadata extension shell for ADP-005, staleness detection contract, and Git policy. EKM runtime and View Model are implemented in `src/ekm/`; migration tooling remains future work.

---

## ADP-003: Engineering Notebook User Interface

**Status:** Accepted (v1.0, 2026-07-28), ratified by ADR-0006, builds on ADP-001

ADP-003 defines the Engineering Notebook as the primary human interface to the EKM, dynamically generated from EKM content with no hard-coded engineering pages. Track D implementation is complete except dockable KiCad action plugin shell (Phase 2). Widget ready in `src/ui/notebook_panel.py`.

---

## ADP-008: AI Engineering Reasoning Framework (AERF)

**Status:** Accepted (v1.1, 2026-07-29), ratified by ADR-0007, builds on ADP-001

ADP-008 defines AERF as a standardized eight-stage engineering reasoning process. Orchestration, per-stage prompts (ADP-007), classifier, Blocking Oscillator KB, and EKM write-back are implemented. Analog simulation closed loop is implemented under ADP-006; firmware-aware mixed-domain simulation is proposed under ADP-014.

---

## ADP-009: Host Integration Layer

**Status:** Accepted (v1.0, 2026-07-29), ratified by ADR-0009, builds on Platform Architecture and ADP-001

ADP-009 defines the Host Integration Layer contract: `DesignSnapshot` protocol (implemented), host responsibilities, and KiCad as reference implementation. `HostLink` generalization deferred until a second host is actively developed.

---

## ADP-010: Engineering Inference Engine (EIE)

**Status:** Accepted (v1.0, 2026-07-29), ratified by ADR-0009, builds on ADP-008 and ADP-009

ADP-010 defines EIE as the platform runtime orchestrator. Chat, simulation/SUBCKT, AERF pipeline, and EKM write-back are implemented in `src/inference/` and `src/ekm/`. Analog simulation closed loop is implemented under ADP-006; firmware-aware mixed-domain simulation (ADP-014) is proposed.

---

## ADP-006: Simulation Abstraction

**Status:** Approved (v1.0, 2026-08-07), builds on ADP-008, ADP-009, ADP-010

Defines host-agnostic simulation abstraction and closed-loop stage refinement. SPICE netlist export, SUBCKT pipeline, and analog closed loop are implemented. Extends to firmware/digital domain via ADP-014 (proposed).

---

## ADP-014: Firmware-Aware Mixed-Domain Simulation

**Status:** Proposed (v1.0, 2026-08-27), builds on ADP-006, ADP-008, ADP-010, Platform Architecture

Defines Digital Control Behavior Model (DCBM) and Level 1–3 MCU simulation maturity (static timing → behavioral controller → firmware co-simulation). DCBM artifact and firmware→stimuli pipeline not yet implemented. Reference validation fixture: `examples/bedini_babcock/firmware/pico_gpio_stub/`.

---

## ADP-007: AERF Prompt Integration and EKM Write-Back

**Status:** Accepted (v1.0, 2026-08-07), builds on ADP-002, ADP-008, ADP-010

Documents per-stage AERF prompts (`src/prompts/templates/aerf_stage.py`) and EKM write-back mapping (`src/ekm/aerf_writeback.py`). Implementation complete.

---

## ADP-011: Assistant Shell User Interface

**Status:** Partial (v1.0, 2026-07-31) — Phase 1 scaffold (`assistant_shell.py`, `--ui`); embedded tabs Phase 2

Defines unified tabbed Assistant shell replacing launcher + separate modals. Target for Phase 2 dockable plugin and `--ui` consolidation.

---

# 5. Cross-Reference Map

## Hub and index documents

- `docs/Architecture/README.md` is the central index linking to all major architecture documents, ADRs, ADPs, and `ARCHITECTURE_DECISIONS.md` at the repository root.
- `docs/Architecture/ADRs/README.md` indexes all ten ADRs with status and date.
- `docs/Architecture/Platform_Architecture.md` is the authoritative platform overview above KiCad-specific documents.

## ADP ↔ ADR ratification pairs

| ADP | Ratified by ADR |
|-----|-----------------|
| ADP-001 (EKM Foundation) | ADR-0005 |
| ADP-002 (EKM Schema and Persistence) | ADR-0008 |
| ADP-003 (Engineering Notebook UI) | ADR-0006 |
| ADP-006 (Simulation Abstraction) | — (proposed) |
| ADP-014 (Firmware-Aware Mixed-Domain Simulation) | — (proposed) |
| ADP-007 (AERF Prompt Integration) | — (retrospective ADP) |
| ADP-008 (AERF) | ADR-0007 |
| ADP-009 (Host Integration Layer) | ADR-0009 |
| ADP-010 (EIE) | ADR-0009 |
| ADP-011 (Assistant Shell UI) | — (proposed) |

Each ADR summarizes and records acceptance of its corresponding ADP; the ADPs contain full architectural rationale.

## ADP dependency chain (documented in ADP-001 Appendix A)

```
ADP-001 → ADP-002 (accepted)
ADP-001 → ADP-003, ADP-004, ADP-005, ADP-006, ADP-007, ADP-008
ADP-002 → ADP-003, ADP-004, ADP-005, ADP-006, ADP-007
ADP-003 → ADP-004
ADP-005 → ADP-007
ADP-008 → ADP-007, ADP-006
ADP-006 → ADP-014
```

ADP-003 depends on ADP-001 and ADP-002 (ratified). ADP-008 builds on ADP-001; ADP-007 documents prompt integration (implemented). ADP-006 covers analog simulation closed loop (implemented). ADP-014 extends ADP-006 into firmware-aware mixed-domain simulation (proposed).

## Software Architecture as component hub

`KiCad_AI_Integration_Software_Architecture.md` references and is referenced by nearly all architecture documents. It defines six major components (Context Collection Engine, Project Context Model, Prompt Builder, AI Provider Layer, Conversation Manager, KiCad User Interface) plus a proposed AERF Orchestrator. ADRs ADR-0004 and ADP-008 link into specific components.

## Phase 1 foundation ADRs (2026-07-14)

ADR-0001 (KiCad 8+), ADR-0002 (Provider Layer), ADR-0003 (Stateless Phase 1), and ADR-0004 (Multimodal Context) form the Phase 1 architectural baseline. They cross-reference each other and connect to:

- `AI_Provider_Interface.md` (implements ADR-0002)
- `Prompt_Architecture.md` (implements multimodal and template guidance per ADR-0003, ADR-0004)
- `Roadmap.md` (phase summary per ADR-0003)

## EKM / Notebook / AERF cluster (2026-07-28)

ADR-0005, ADR-0006, ADR-0007 and ADP-001, ADP-003, ADP-008 form a second architectural cluster around persistent engineering knowledge and staged reasoning:

- ADP-001 defines EKM authority boundaries with `ProjectContext` and Conversation Manager
- ADP-003 defines Notebook UI as EKM presentation layer
- ADP-008 defines AERF as reasoning layer feeding EKM after approval
- All three ADPs reference `Prompt_Architecture.md` for prompt integration ([ADP-007](docs/Architecture/ADP-007-AERF-Prompt-Integration.md))

## External domain references (outside docs/Architecture/)

| External path | Referenced from |
|---------------|-----------------|
| `ARCHITECTURE_DECISIONS.md` | Architecture README, ADRs README |
| `PROJECT_INDEX.md`, `README.md`, `PROJECT_CHARTER.md` | Most documents (navigation) |
| `tasks/MASTER_TASK_LIST.md` | Software Architecture, Roadmap, Prompt Architecture, AI Provider Interface, ADRs, ADPs |
| `docs/AI/Security.md` | ADP-001, ADP-003, ADP-008, ADR-0004, ADR-0005, ADR-0006, AI Provider Interface |
| `docs/AI/Prompting_Guide.md`, `docs/AI/Cost_Optimization.md` | Prompt Architecture |
| `docs/Specifications/Netlist_Gap_Fill.md` | Software Architecture, Prompt Architecture |
| `docs/Developer_Handbook/` | Software Architecture, ADR-0001, Prompt Architecture |
| `docs/Database/README.md` | ADP-001, ADP-003, ADR-0005, ADR-0006 |
| `docs/Engineering_Knowledge/` | ADP-001, ADP-008, ADR-0007, Prompt Architecture; includes `Engineering_Reasoning_Methodology.md` |
| `src/` code paths | ADP-001 (`src/context/model.py`, `src/prompts/templates/general_review.py`), AI Provider Interface (`src/providers/`) |

## Reference direction summary

```
README.md (index)
    ├── Platform_Architecture.md (platform overview)
    │       ├── ADP-009 (Host Integration Layer) ──ratified──► ADR-0009
    │       └── ADP-010 (EIE) ──ratified──► ADR-0009
    ├── KiCad_AI_Integration_Software_Architecture.md (KiCad host view)
    │       ├── ADRs 0001–0004 (Phase 1 decisions)
    │       └── ADP-008 (AERF orchestrator, proposed)
    ├── Prompt_Architecture.md
    │       ├── ADRs 0003, 0004
    │       └── ADP-008 (future stage templates)
    ├── AI_Provider_Interface.md
    │       └── ADR-0002
    ├── Roadmap.md
    │       └── ADR-0003, ADP-008
    ├── ADP-001 (EKM) ──ratified──► ADR-0005
    │       ├── ADP-003 (Notebook UI) ──ratified──► ADR-0006
    │       └── ADP-008 (AERF) ──ratified──► ADR-0007
    └── ADRs/README.md (ADR index)
```

---

# 6. Architecture Coverage

The following architecture topics are documented under `docs/Architecture/`:

## System overview and phasing

- Project goals and long-term vision for an AI-assisted engineering environment inside KiCad
- Three-phase delivery model: Phase 1 (Python script MVP), Phase 2 (native plugin with chat), Phase 3 (advanced engineering assistant)
- Phase boundaries, exit criteria, and component scope per phase

## Major software components

- Context Collection Engine (KiCad data extraction: schematic, PCB, netlist, BOM, ERC, DRC)
- Project Context Model (internal structured representation including optional schematic image)
- Prompt Builder (token optimization, templates, chunking)
- AI Provider Layer (abstract interface, Claude implementation)
- Conversation Manager (deferred to Phase 2)
- KiCad User Interface (wxPython dialog → dockable chat window)
- AERF Orchestrator (implemented — `src/reasoning/`, `src/inference/aerf.py`)

## AI provider integration

- Abstract `send_message` contract and factory pattern
- Configuration schema (`~/kicad_ai_config.json`, environment overrides)
- Response model (`ProviderResponse`, `TokenUsage`)
- Error handling taxonomy (`AuthError`, `RateLimitError`, `TimeoutError`, etc.)
- Multimodal image attachment support
- Phase 1 stateless provider usage

## Prompt construction

- XML-style structured prompt sections (`<functional_description>`, `<kicad_python_extracted_data>`, etc.)
- Named engineering audit templates (general review implemented; others planned)
- Multimodal schematic image inclusion criteria and export pipeline
- Netlist gap-fill prompt templates (connectivity inference, SUBCKT generation tiers A/B/C)
- Future AERF stage prompt templates — implemented ([ADP-007](docs/Architecture/ADP-007-AERF-Prompt-Integration.md))
- Token budgeting strategies (planned)

## Platform architecture

- Three-layer model: Platform / Frameworks / Host Integrations
- KiCad AI Integration as first host reference implementation
- `DesignSnapshot` host-neutral contract (`src/platform_core/contracts.py`)
- Engineering Inference Engine (EIE) as runtime orchestrator separate from AERF methodology
- Import boundaries between platform and host modules
- Future host patterns (CLI, web, laboratory, other EDA tools)
- Physical `src/hosts/` reorganization deferred until second host

## Platform and dependencies

- KiCad 8+ minimum version requirement
- External tool dependencies (`kicad-cli`, Poppler `pdftoppm`)
- Schematic image export at 600 DPI default

## Security and approval

- No hardcoded API keys; secure credential storage
- No automatic cloud transmission; explicit user approval (Approve & Send)
- Opt-in multimodal context
- EKM and AERF cloud transmission and write-back approval requirements

## Engineering Knowledge Model (EKM)

- Canonical engineering knowledge representation separate from KiCad connectivity
- Layering: User → Notebook UI → View Model → EKM → JSON persistence
- Authority boundaries (KiCad, ProjectContext, EKM, Conversation Manager, artifact library)
- Minimum metamodel (sections, typed fields, links, metadata extension points)
- Domain independence and extensibility
- JSON persistence under `kicad_ai/` with `schema_version`
- Relationship to `ProjectContext` and Conversation Manager
- Deferred topics: provenance (ADP-004), NL conversion (ADP-005), firmware-aware mixed-domain simulation (ADP-014); prompt integration (ADP-007) and analog simulation closed loop (ADP-006) implemented

## Engineering Notebook UI

- Dynamic rendering from EKM (no hard-coded pages)
- View Model and Notebook Renderer separation
- Primitive field type registry and presentation mapping
- Artifact library references for binary content
- Editing pathway and AI mutation approval
- KiCad dockable panel integration; chat as sibling surface
- Navigation, search, filtering (planned)
- Advanced JSON View for debugging only

## AI Engineering Reasoning Framework (AERF)

- Eight canonical reasoning stages (0–7) with stable IDs and overridable titles
- Stage execution model with accumulated context and partial runs
- Internal engineering reasoning methodology and knowledge classification (10 types)
- Evidence chains for traceable, explainable conclusions
- Scientific neutrality and integrity principle (no misrepresentation of evidentiary status)
- Per-stage JSON output contract
- Circuit family overlay model and recognition (conceptual, deferred)
- Knowledge loading from `docs/Engineering_Knowledge/Circuit_Families/`
- Simulation philosophy (reason first, validate second)
- Coexistence with `general_review` ad-hoc template
- EKM write-back mapping from stage conclusions
- Deferred: orchestrator (`src/reasoning/`), classifier, per-stage prompts (ADP-007)

## Architecture decision governance

- Nine accepted ADRs covering platform foundation, KiCad version, provider abstraction, Phase 1 statelessness, multimodal context, EKM, Notebook UI, AERF, and EKM schema
- Five accepted ADPs (001, 002, 003, 008, 009, 010) with full architectural proposals ratified by ADRs
- Deferred ADP numbering (002–007) documented in ADP-001 Appendix A

---

# 7. README Files

## docs/Architecture/README.md

**Purpose:** Primary index and navigation entry point for the Architecture documentation domain. Lists all authoritative architecture documents, ADRs, and ADPs with links. Defines what content belongs in this folder (component design, phase roadmaps, ADRs, ADPs) and includes maintenance guidance to update the index when documents are created, moved, renamed, or retired.

## docs/Architecture/ADRs/README.md

**Purpose:** Index for the Architecture Decision Records subdirectory. Contains a table of all ten ADRs with ID, decision title, status (all Accepted), and date. Provides navigation links back to the project index, Architecture README, and root `ARCHITECTURE_DECISIONS.md`.

---

# 8. Executive Summary

The `docs/Architecture/` directory contains **24 Markdown files** organized into a root-level index, six topical architecture documents, nine Architectural Design Proposals (ADPs), and ten Architecture Decision Records (ADRs) plus an ADR index.

**Document types and status:**

- **Index documents (2):** `README.md` files at the Architecture root and in `ADRs/` serve as navigation hubs.
- **Top-level architecture (6):** Platform Architecture is Canonical; Software Architecture (KiCad host) and Roadmap are Draft; Prompt Architecture and AI Provider Interface document implemented Phase 1 behavior.
- **ADPs (11+):** ADP-001 through ADP-003, ADP-006 through ADP-011, ADP-013, ADP-014 are Accepted or Proposed; ADP-014 (firmware-aware mixed-domain simulation) added 2026-08-27.
- **ADRs (10):** All Accepted. ADR-0001 through ADR-0004 establish Phase 1 foundation. ADR-0005 through ADR-0008 ratify EKM, Notebook, AERF, and EKM schema. ADR-0009 ratifies platform architecture foundation. ADR-0010 ratifies AERP umbrella acronym.

**Architectural themes documented:** In-KiCad AI assistant with phased delivery; context collection from KiCad projects; structured prompt construction with optional multimodal schematic images; provider abstraction starting with Claude; persistent engineering knowledge via EKM and Engineering Notebook UI; staged circuit analysis via AERF with circuit-family knowledge overlays; explicit security and user-approval boundaries for cloud transmission.

**Cross-referencing:** Documents are heavily interlinked. `README.md` is the central hub. ADPs and ADRs form ratification pairs. ADP-001 Appendix A documents a dependency graph for future ADPs. Multiple documents reference external domains (`docs/AI/`, `docs/Engineering_Knowledge/`, `docs/Database/`, `docs/Specifications/`, `tasks/MASTER_TASK_LIST.md`, and source code paths).

**Implementation state as documented:** Phase 1 components and Tracks B–D (EKM runtime, Notebook UI, AERF orchestration, EIE, ADP-007 write-back, ADP-006 analog closed loop) are implemented. Firmware-aware mixed-domain simulation (ADP-014), unified Assistant shell completion (ADP-011), and Conversation Manager remain open.
