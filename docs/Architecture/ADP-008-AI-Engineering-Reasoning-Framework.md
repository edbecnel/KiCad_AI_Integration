# ADP-008: AI Engineering Reasoning Framework (AERF)

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Architecture](README.md) › ADP-008

**Status:** Accepted (v1.1 — engineering reasoning methodology)

**Author:** Ed Becnel

**Project:** KiCad AI Integration Plugin

**Version:** 1.1

**Date:** 2026-07-29

**Ratified by:** [ADR-0007](ADRs/ADR-0007-AERF-Foundation.md)

**Builds on:** [ADP-001: Engineering Knowledge Model Foundation](ADP-001-Engineering-Knowledge-Model-Foundation.md) (v1.1)

**Related:** [Engineering Knowledge](../Engineering_Knowledge/README.md) documentation domain, [Engineering Reasoning Methodology](../Engineering_Knowledge/Engineering_Reasoning_Methodology.md)

---

## 1. Purpose

This Architectural Design Proposal (ADP) defines the **AI Engineering Reasoning Framework (AERF)**, a standardized sequence of engineering reasoning stages that the AI follows before producing conclusions or recommendations about a circuit.

AERF is a **reasoning process and ontology**, not a replacement for KiCad, simulation engines, or the Engineering Knowledge Model (EKM). It defines *how* the plugin progressively builds engineering understanding rather than immediately sending a schematic to a large language model for a single-shot answer.

Runtime orchestration, per-stage prompt templates, and circuit family classification are implemented per [ADP-007](ADP-007-AERF-Prompt-Integration.md) and `src/reasoning/classifier.py`. Simulation closed loop remains under [ADP-006](ADP-006-Simulation-Abstraction.md).

---

## 2. Background

During development of layered engineering documentation for power-electronics circuits, an important architectural insight emerged: the documentation structure mirrors how experienced electrical engineers analyze unfamiliar circuits.

Engineers do not jump directly to conclusions. They:

1. Identify what the circuit is
2. Explain how it operates
3. Trace energy and signal flow
4. Ground behavior in physical principles
5. Assign roles to each component
6. Consider operating modes and edge cases
7. Expand analysis to the complete system
8. Draw engineering conclusions, recommend measurements, and suggest improvements

The KiCad AI Integration project should emulate this structured reasoning process rather than functioning as a generic LLM wrapper.

---

## 3. Problem Statement

Single-shot AI prompts on raw schematic context produce:

- Opaque conclusions without traceable reasoning
- Premature simulation requests without engineering understanding
- Non-reusable analysis that does not generalize across circuit families
- Conflation of extracted KiCad facts with engineering interpretation

The project needs a first-class architectural component that defines **staged, explainable, reusable engineering reasoning** independent of any specific circuit.

---

## 4. Goals

AERF shall:

- Define a canonical sequence of eight reasoning stages (0–7)
- Support circuit-family-specific knowledge overlays while preserving stage identity
- Accumulate structured reasoning artifacts across stages
- Feed curated conclusions into the EKM after user approval
- Treat simulation as validation of prior reasoning, not a substitute for it
- Remain independent of any single circuit family or engineering discipline
- Provide explainable, transparent analysis that distinguishes this project from conventional AI-assisted schematic tools

---

## 5. Non-Goals

AERF is NOT intended to:

- Replace the KiCad schematic or `ProjectContext` extraction
- Replace the Engineering Knowledge Model (EKM)
- Replace ngspice, KiCad's simulator, or other simulation engines
- Embed circuit-family domain logic in plugin code
- Mandate full eight-stage analysis for every user question (partial runs are allowed)
- Replace the `general_review` ad-hoc chat template for simple questions

---

## 6. Architecture

AERF sits between context collection and EKM population:

```
KiCad Project
   │
   ▼
Context Collection Engine → ProjectContext
   │
   ▼
Circuit Family Recognition (heuristic classifier + user hint + EKM prior)
   │
   ▼
Load Circuit Family Knowledge Base (reference content)
   │
   ▼
AERF Stages 0–7 (sequential, accumulated context)
   │
   ├── Open Questions
   ├── Simulation Requests (validate/refine prior stages)
   └── Engineering Conclusions
   │
   ▼
User Approval
   │
   ▼
EKM Write-back (curated project knowledge)
```

AERF stage outputs are **transient reasoning artifacts** during an analysis session. The EKM stores **curated, user-approved conclusions** distilled from those artifacts.

See [ADP-001 §6](ADP-001-Engineering-Knowledge-Model-Foundation.md#6-architecture) for the EKM layering diagram. AERF is the reasoning layer that operates on `ProjectContext` and Circuit Family KB before conclusions enter the EKM.

---

## 7. Authority Boundaries

| Store | Owns | Lifetime |
|-------|------|----------|
| KiCad schematic | Electrical connectivity | Design lifetime |
| `ProjectContext` | Extracted KiCad facts (symbols, netlist, datasheets, PCB summary) | Per request / refresh |
| Circuit Family KB | Reusable domain reference knowledge | Repository lifetime |
| AERF stage outputs | Per-analysis reasoning artifacts | Session / optional archive |
| EKM | Curated engineering knowledge (intent, rationale, assumptions, decisions) | Project lifetime |
| Simulation results | Validated measurements and waveforms | Project lifetime (via [ADP-006](ADP-006-Simulation-Abstraction.md), closed loop deferred) |
| Conversation Manager | Raw multi-turn chat transcripts | Session / optional archive |

Per [ADP-001 §18](ADP-001-Engineering-Knowledge-Model-Foundation.md#18-relationship-to-conversation-manager), conversations are **input**; the EKM is **distilled output** after user approval. AERF stage outputs are intermediate reasoning — not automatically persisted to the EKM.

---

## 8. Canonical Reasoning Stages

Each stage has a stable `stage_id` (integer 0–7), a `stage_key` (snake_case identifier), a default `title`, and a guiding `question`.

Circuit families may override stage **titles** for stages 1–6 (for example, "Signal Flow" instead of "Energy Flow" for operational amplifiers) while preserving `stage_id` and dependency order.

### Stage summary

| stage_id | stage_key | Default title | Question |
|----------|-----------|---------------|----------|
| 0 | `circuit_identification` | Circuit Identification | What is this circuit? |
| 1 | `basic_operation` | Basic Operation | How does it work? |
| 2 | `energy_flow` | Energy Flow | Where does the energy go? |
| 3 | `physical_principles` | Physical Principles | Why does it behave this way? |
| 4 | `component_roles` | Component Roles | What does every component contribute? |
| 5 | `operating_modes` | Operating Modes | How does behavior change? |
| 6 | `system_behavior` | System Behavior | How does the complete system behave? |
| 7 | `engineering_analysis` | Engineering Analysis | What conclusions can an experienced engineer draw? |

Full stage definitions with required determinations and output schemas are maintained in [`docs/Engineering_Knowledge/AERF_Stage_Index.md`](../Engineering_Knowledge/AERF_Stage_Index.md).

---

## 9. Stage Execution Model

### Sequential accumulation

Stages execute in order (0 → 7). Each stage prompt receives:

- `ProjectContext` (extracted KiCad facts)
- Relevant Circuit Family KB excerpts for the current stage
- Prior stage JSON outputs (stages 0 through N−1)
- Existing EKM sections (if present)
- Optional user hints or functional description

### Internal Engineering Reasoning Methodology

Every AERF stage executes using a common engineering reasoning methodology defined in [Engineering Reasoning Methodology](../Engineering_Knowledge/Engineering_Reasoning_Methodology.md).

The stage defines **what** engineering questions must be answered. The Engineering Reasoning Methodology defines **how** those answers are produced.

Regardless of circuit family or engineering discipline, each stage follows a consistent reasoning process including:

- Collection of available evidence
- Classification of observations
- Formation of one or more engineering hypotheses
- Evaluation of competing hypotheses
- Topology recognition
- Component interaction analysis
- Energy and signal path tracing
- Confidence estimation
- Identification of unknowns
- Identification of contradictory evidence
- Generation of traceable engineering conclusions

The reasoning methodology shall distinguish between:

- Direct observations
- Derived conclusions
- Engineering assumptions
- User-provided information
- Circuit-family knowledge
- Outstanding unknowns

Every engineering conclusion should be traceable back to the observations and reasoning that produced it. Significant determinations should carry knowledge classification and evidence chains per the methodology document. The objective is explainable engineering reasoning rather than opaque AI conclusions.

### Scientific neutrality

AERF remains scientifically neutral. It does not arbitrate which scientific theory is ultimately correct. It classifies every conclusion according to evidentiary status, respects project design intent, and reasons transparently within the selected theoretical framework. Full treatment is in [Engineering Reasoning Methodology §6](../Engineering_Knowledge/Engineering_Reasoning_Methodology.md#6-scientific-neutrality-principle).

### Partial runs

Users may request analysis through Stage N only (for example, Stages 0–1 for quick circuit triage). The orchestrator must not require completion of all eight stages for every request.

### Per-stage output contract

Every stage produces a JSON artifact with this minimum structure:

```json
{
  "stage_id": 0,
  "stage_key": "circuit_identification",
  "title": "Circuit Identification",
  "question": "What is this circuit?",
  "determinations": {},
  "open_questions": [],
  "confidence": "high|medium|low",
  "unknowns": [],
  "simulation_hooks": [],
  "sources": ["project_context", "circuit_family_kb", "prior_stages", "ekm"]
}
```

- `determinations` — stage-specific structured content (schema defined per stage in the Stage Index); significant determinations should carry knowledge classification and evidence chains per [Engineering Reasoning Methodology](../Engineering_Knowledge/Engineering_Reasoning_Methodology.md) (prompt/write-back contract in [ADP-007](ADP-007-AERF-Prompt-Integration.md))
- `open_questions` — items requiring user input, measurement, or further analysis
- `confidence` — overall confidence for this stage's conclusions
- `unknowns` — explicitly flagged gaps; the AI must not fabricate information to fill these (see [Integrity Principle](../Engineering_Knowledge/Engineering_Reasoning_Methodology.md#8-integrity-principle))
- `simulation_hooks` — optional suggestions for simulations that would validate or refine this stage (not a substitute for determinations)
- `sources` — which inputs informed this stage's reasoning

### Human approval gates

- Cloud transmission for each stage (or batch of stages) requires explicit user approval, consistent with [ADR-0005](ADRs/ADR-0005-EKM-Foundation.md) and the existing Approve & Send pattern.
- EKM write-back from Stage 7 conclusions requires separate user approval.

---

## 10. Circuit Family Overlay Model

### Concept

A **circuit family** is a reusable engineering ontology (for example, Blocking Oscillator, Flyback, Buck Converter, Operational Amplifier). Each family provides reference knowledge organized by AERF stage.

Families share the same stage IDs and dependency order. They may differ in:

- Stage titles (stages 1–6)
- Domain-specific determinations within each stage
- Recognition signatures (component patterns, topology heuristics)
- Reference equations, typical waveforms, and failure modes

### Example title overlays

| stage_id | Blocking Oscillator | Operational Amplifier | Digital Logic |
|----------|--------------------|-----------------------|---------------|
| 1 | Basic Oscillation | Basic Operation | Logic Operation |
| 2 | Energy Flow | Signal Flow | Timing Analysis |

Stage 0 (`circuit_identification`) and Stage 7 (`engineering_analysis`) titles are fixed across families.

### Planned circuit families

Registry entries (content deferred):

- `Blocking_Oscillator`
- `Flyback`
- `Buck`
- `Boost`
- `Linear_Regulator`
- `Operational_Amplifier`
- `Audio_Amplifier`
- `Digital_Logic`

See [`docs/Engineering_Knowledge/Circuit_Families/README.md`](../Engineering_Knowledge/Circuit_Families/README.md).

---

## 11. Circuit Family Recognition

Circuit family recognition selects family-specific KB content before staged analysis. Heuristic classifier implemented in `src/reasoning/classifier.py`; user hints and EKM context remain supported inputs.

### Inputs

- Topology heuristics from `ProjectContext` (component types, net names, feedback paths)
- Component value signatures (inductor/transformer presence, switching devices, op-amp symbols)
- User-provided hint (for example, "this is a flyback converter")
- Prior EKM content (if the family was previously identified for this project)
- Optional schematic image (multimodal context per [ADR-0004](ADRs/ADR-0004-Optional-Multimodal-Schematic-Context.md))

### Output

```json
{
  "family_id": "flyback",
  "family_label": "Flyback Converter",
  "confidence": "high|medium|low",
  "alternatives": [{"family_id": "buck", "confidence": "low"}],
  "recognition_basis": ["transformer_primary_secondary", "switching_node", "output_rectifier"]
}
```

When confidence is low, Stage 0 should proceed with generic identification and flag the family as uncertain in `unknowns`.

---

## 12. Knowledge Loading Contract

Circuit Family KB content lives under:

```text
docs/Engineering_Knowledge/Circuit_Families/<Family_Name>/
```

### Per-family file structure

```text
<Family_Name>/
├── README.md                      # Family overview, recognition signatures
├── 00_Circuit_Identification.md
├── 01_<FamilySpecificStageTitle>.md
├── 02_<FamilySpecificStageTitle>.md
├── ...
└── 07_Engineering_Analysis.md
```

### File naming rules

- Prefix: two-digit `stage_id` (`00` through `07`)
- Suffix: underscore-separated title matching the family's stage overlay or default title
- `README.md` at family root: overview, recognition signatures, related families

### Loading behavior (conceptual)

1. Resolve `family_id` from recognition output
2. Load `README.md` for family context
3. For each stage N in the requested range, load `0N_*.md` and inject relevant excerpts into the stage N prompt
4. If family KB is missing for a stage, fall back to generic stage guidance from `AERF_Stage_Index.md`

KB content is **reference material** — not per-project instance data. The orchestrator selects excerpts; it does not embed the entire KB in every prompt.

---

## 13. Simulation Philosophy

Simulation supports AERF; it does not replace it.

### Principles

1. **Reason first** — Stages 0–6 establish engineering understanding before simulation is requested.
2. **Validate and refine** — Simulation results from Stage 7 (or earlier `simulation_hooks`) confirm, challenge, or refine prior determinations.
3. **Never substitute** — The AI must not defer Stage 3 (Physical Principles) or Stage 4 (Component Roles) to "run a simulation and see."
4. **Explicit hooks** — Each stage may emit `simulation_hooks` describing what to simulate, expected outcomes, and which prior determination would be validated.
5. **Closed loop** — Per [ADP-006](ADP-006-Simulation-Abstraction.md), simulation results feed back into stage refinement (implemented). [ADP-014](ADP-014-Firmware-Aware-Mixed-Domain-Simulation.md) adds firmware-aware mixed-domain simulation on top — DCBM and Level 1 static timing are proposed, not yet implemented.

### Relationship to existing SUBCKT workflow

The two-stage SUBCKT generation pipeline (`facts` → `synthesis` in `subckt_generation.py`) is a **precedent** for staged LLM orchestration. SUBCKT generation is a **tooling workflow** (model creation), not an AERF stage. AERF Stage 7 may *request* SUBCKT models via `simulation_hooks` when simulation is needed.

---

## 14. Relationship to Prompt Architecture

Each AERF stage maps to a named prompt template ([ADP-007](ADP-007-AERF-Prompt-Integration.md)). Prompts use structured XML-style sections per [Prompt Architecture](Prompt_Architecture.md):

- `<aerf_stage>` — current stage metadata (id, key, title, question)
- `<aerf_prior_stages>` — accumulated JSON from stages 0 through N−1
- `<circuit_family_kb>` — excerpts from the loaded family KB
- `<kicad_python_extracted_data>` — `ProjectContext` JSON
- `<engineering_knowledge>` — relevant EKM sections (when present)
- `<user_question>` — optional user focus for this stage

Stage prompt templates are implemented in [`src/prompts/templates/aerf_stage.py`](../../src/prompts/templates/aerf_stage.py) per [ADP-007](ADP-007-AERF-Prompt-Integration.md).

---

## 15. Relationship to EKM

AERF produces transient reasoning artifacts. The EKM stores curated conclusions.

### Mapping (implemented; see [ADP-007](ADP-007-AERF-Prompt-Integration.md) §6)

| AERF output | EKM destination |
|-------------|-----------------|
| Stage 0 determinations (family, topology, I/O) | EKM section: Circuit Overview |
| Stage 1–3 determinations | EKM section: Operation and Principles |
| Stage 4 determinations | EKM section: Component Rationale (per-ref fields with links) |
| Stage 5–6 determinations | EKM section: Operating Conditions |
| Stage 7 conclusions | EKM sections: Analysis, Recommendations, Open Items |
| `open_questions` | EKM fields with status `Pending Review` |

Write-back requires user approval per [ADP-001 §14](ADP-001-Engineering-Knowledge-Model-Foundation.md#14-security-and-approval).

---

## 16. Coexistence with `general_review`

The existing `general_review` prompt template remains valid for:

- Quick ad-hoc questions
- Narrow scope inquiries (for example, "what is the purpose of R3?")
- Development smoke tests

AERF is the **structured path** for deep circuit analysis. The plugin should offer both modes. `general_review` is not a substitute for a full AERF analysis when the user requests comprehensive engineering reasoning.

---

## 17. Domain Independence

Consistent with [ADP-001 §9](ADP-001-Engineering-Knowledge-Model-Foundation.md#9-domain-independence):

- The plugin orchestrator is **domain-agnostic** — it executes stages, loads KB files, and accumulates JSON.
- Circuit-family domain content lives in `docs/Engineering_Knowledge/`, not in plugin code.
- New circuit families require **documentation and KB content only**, not plugin changes.

---

## 18. Security and Approval

- Each AERF stage (or approved batch) requires explicit user approval before cloud transmission.
- Circuit Family KB excerpts included in prompts must be visible in the context preview.
- EKM write-back from AERF conclusions requires separate approval.
- AERF must not auto-transmit `ProjectContext`, KB content, or stage outputs.

See [Security](../AI/Security.md).

---

## 19. Implementation

| Component | Status | Location / ADP |
|-----------|--------|----------------|
| AERF stage registry + KB loader | Implemented | `src/reasoning/` |
| AERF orchestration + approval gating | Implemented | `src/inference/aerf.py` |
| Per-stage prompt templates | Implemented | [ADP-007](ADP-007-AERF-Prompt-Integration.md), `src/prompts/templates/aerf_stage.py` |
| Circuit family classifier | Implemented | `src/reasoning/classifier.py` |
| EKM stage-output mapping / write-back | Implemented | [ADP-007](ADP-007-AERF-Prompt-Integration.md), `src/ekm/aerf_writeback.py` |
| Simulation closed loop | Deferred | [ADP-006](ADP-006-Simulation-Abstraction.md) |
| First circuit family KB (Blocking Oscillator) | Implemented | `docs/Engineering_Knowledge/Circuit_Families/Blocking_Oscillator/` |

---

## 20. Decision

**Accepted (v1.1)**

This ADP establishes the AI Engineering Reasoning Framework as a foundational architectural pillar of the KiCad AI Integration project, alongside the Engineering Knowledge Model. Version 1.1 adds the internal engineering reasoning methodology layer without changing stage structure or authority boundaries.

All future deep circuit analysis, prompt integration, and simulation workflows shall build upon AERF staged reasoning.

Ratified as [ADR-0007: AERF Foundation](ADRs/ADR-0007-AERF-Foundation.md).

---

## Appendix A: Per-Stage Determinations (Summary)

Detailed schemas are in [`AERF_Stage_Index.md`](../Engineering_Knowledge/AERF_Stage_Index.md).

### Stage 0 — Circuit Identification

**Determinations:** `family_id`, `topology`, `functional_blocks[]`, `inputs[]`, `outputs[]`, `switching_method`, `energy_storage_method`

### Stage 1 — Basic Operation

**Determinations:** `operating_sequence`, `startup_behavior`, `switching_mechanism`, `oscillation_cycle` (if applicable), `control_mechanism`

### Stage 2 — Energy Flow

**Determinations:** `energy_source`, `storage_elements[]`, `transfer_path`, `losses[]`, `outputs[]`

### Stage 3 — Physical Principles

**Determinations:** `magnetic_behavior`, `electric_field_interactions`, `semiconductor_physics`, `governing_equations[]`

### Stage 4 — Component Roles

**Determinations:** `components[]` with `reference`, `purpose`, `interactions[]`, `design_intent`, `possible_substitutions[]`

### Stage 5 — Operating Modes

**Determinations:** `modes[]` covering startup, steady state, fault conditions, loading changes, component failures, environmental changes

### Stage 6 — System Behavior

**Determinations:** `mechanical_interactions`, `thermal_effects`, `environmental_influences`, `external_systems[]`

### Stage 7 — Engineering Analysis

**Determinations:** `performance_evaluation`, `failure_analysis`, `optimization_suggestions[]`, `simulation_interpretation`, `measurement_recommendations[]`, `design_improvements[]`, `conclusions[]`

---

## Related Documents

- [ADR-0007: AERF Foundation](ADRs/ADR-0007-AERF-Foundation.md)
- [ADP-001: Engineering Knowledge Model Foundation](ADP-001-Engineering-Knowledge-Model-Foundation.md)
- [Prompt Architecture](Prompt_Architecture.md)
- [Software Architecture](KiCad_AI_Integration_Software_Architecture.md)
- [Engineering Knowledge](../Engineering_Knowledge/README.md)
- [AERF Stage Index](../Engineering_Knowledge/AERF_Stage_Index.md)
- [Engineering Reasoning Methodology](../Engineering_Knowledge/Engineering_Reasoning_Methodology.md)
- [Circuit Families](../Engineering_Knowledge/Circuit_Families/README.md)
- [ADP-006: Simulation Abstraction](ADP-006-Simulation-Abstraction.md)
- [ADP-014: Firmware-Aware Mixed-Domain Simulation](ADP-014-Firmware-Aware-Mixed-Domain-Simulation.md)
- [Master Task List](../../tasks/MASTER_TASK_LIST.md)

## Parent

- [Architecture](README.md)
