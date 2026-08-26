# Glossary and Acronyms

[Home](../../README.md) · [Project Index](../../PROJECT_INDEX.md) · [Reference](README.md)

> **Authoritative terminology reference** for KiCad AI Integration and the AI-assisted Electrical Engineering Reasoning Platform. **AERP** is the umbrella acronym for the host-agnostic framework stack. When other documents define the same term, this glossary is the canonical short form; detailed specifications remain in linked ADPs, ADRs, and architecture docs.

---

## Product and platform

| Term | Expansion / meaning | Notes |
|------|---------------------|-------|
| **AERP** | **A**I-assisted **E**ngineering **R**easoning **P**latform | **Umbrella acronym** for the host-agnostic framework stack (EKM, AERF, EIE, prompts, providers, artifact library, engineering KB, `platform_core`, etc.). Ratified by [ADR-0010](../Architecture/ADRs/ADR-0010-AERP-Platform-Umbrella-Acronym.md). |
| **AI-assisted Electrical Engineering Reasoning Platform** | Product vision | Long-form platform name for charters and formal docs. AERP compresses this for daily use. |
| **KiCad AI Integration** | First host integration | Reference implementation that embeds **AERP** in KiCad. Not the architectural boundary of AERP. |
| **Platform frameworks** | Descriptive collective | Same scope as **AERP** — interchangeable in architecture prose when linked here. |
| **Host integration** | Editor- or environment-specific adapter | KiCad is the first host. Outside AERP. See [ADP-009](../Architecture/ADP-009-Host-Integration-Layer.md). |

### AERP hierarchy (umbrella vs frameworks)

```text
AERP (host-agnostic framework stack)
├── EKM
├── AERF          ← one framework under AERP, not the umbrella
├── EIE
├── Prompt Architecture
├── AI Provider Layer
├── Artifact Library
├── Engineering Knowledge Libraries
└── platform_core (DesignSnapshot, …)

Host integrations (outside AERP)
└── KiCad AI Integration (context/, ui/, …)
```

**AERF ≠ AERP.** Use AERP for the collective; AERF only for staged reasoning (stages 0–7).

### Not used

| Term | Status |
|------|--------|
| **EERP** | **Rejected** — too close to AERF and ERP (enterprise software). Superseded by **AERP**. See [ADR-0009](../Architecture/ADRs/ADR-0009-Platform-Architecture-Foundation.md), [ADR-0010](../Architecture/ADRs/ADR-0010-AERP-Platform-Umbrella-Acronym.md). |
| **Platform** (alone) | **Avoid as spoken umbrella** — too generic (“which platform?”). Prefer **AERP** in conversation; use “platform” only with clear context or as “platform frameworks.” |

---

## Platform frameworks (AERP)

These frameworks are components of **AERP** — the host-agnostic stack. See [AERP hierarchy](#aerp-hierarchy-umbrella-vs-frameworks) above.

| Acronym | Expansion | Role | Primary doc |
|---------|-----------|------|-------------|
| **EKM** | Engineering Knowledge Model | Persistent, per-project curated engineering knowledge (intent, rationale, decisions, links). | [ADP-001](../Architecture/ADP-001-Engineering-Knowledge-Model-Foundation.md) |
| **AERF** | AI Engineering Reasoning Framework | *What* to reason about: eight canonical stages (0–7), circuit-family KB overlays, methodology. | [ADP-008](../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md) |
| **EIE** | Engineering Inference Engine | *How* reasoning runs: orchestration, prompt assembly, provider calls, approval gating. | [ADP-010](../Architecture/ADP-010-Engineering-Inference-Engine.md) |

### Related platform components (not acronyms)

| Term | Meaning | Code / doc |
|------|---------|------------|
| **DesignSnapshot** | Host-neutral protocol for ephemeral extracted design facts (`project_path`, `project_name`, `to_dict()`). | `src/platform_core/contracts.py`, [ADP-009](../Architecture/ADP-009-Host-Integration-Layer.md) |
| **ProjectContext** | KiCad host implementation of `DesignSnapshot`. | `src/context/model.py` |
| **Prompt Architecture** | How design context becomes structured XML-section prompts. | [Prompt_Architecture.md](../Architecture/Prompt_Architecture.md), `src/prompts/` |
| **AI Provider Layer** | Abstract LLM interface (Claude today). | [AI_Provider_Interface.md](../Architecture/AI_Provider_Interface.md), `src/providers/` |
| **Artifact Library** | Content-addressed store for datasheets, SPICE libs, exports. | `src/context/artifacts/` |
| **Engineering Knowledge Libraries** | Circuit-family reference markdown under `docs/Engineering_Knowledge/`. | [Engineering Knowledge](../Engineering_Knowledge/README.md) |
| **Conversation Manager** | Raw multi-turn chat transcripts (input, not canonical knowledge). | Deferred Phase 2+ |

### AERF vs EIE

- **AERF** defines staged reasoning ontology, stage schemas, and KB content — it does not send prompts or call cloud APIs.
- **EIE** executes stages, merges `DesignSnapshot` + EKM + KB excerpts, builds prompts, and invokes providers after user approval.

---

## Documentation types

| Acronym | Expansion | Meaning |
|---------|-----------|---------|
| **EDF** | Engineering Documentation Framework | How this repository organizes `docs/` (domains, navigation, governance). | [ENGINEERING_DOCUMENTATION_FRAMEWORK.md](../../ENGINEERING_DOCUMENTATION_FRAMEWORK.md) |
| **ADR** | Architecture Decision Record | Ratified, durable decision (`docs/Architecture/ADRs/`). Indexed in [ARCHITECTURE_DECISIONS.md](../../ARCHITECTURE_DECISIONS.md). |
| **ADP** | Architectural Design Proposal | Detailed design specification; may precede or accompany an ADR (`docs/Architecture/ADP-*.md`). |

---

## Architecture documents (ADP / ADR)

### Ratified ADPs (documents exist)

| ID | Title |
|----|-------|
| **ADP-001** | Engineering Knowledge Model Foundation |
| **ADP-002** | EKM Schema and Persistence |
| **ADP-003** | Engineering Notebook User Interface |
| **ADP-006** | Simulation Abstraction (analog closed loop implemented) |
| **ADP-014** | Firmware-Aware Mixed-Domain Simulation (proposed — DCBM / Level 1 not implemented) |
| **ADP-007** | AERF Prompt Integration and EKM Write-Back (implemented) |
| **ADP-008** | AI Engineering Reasoning Framework |
| **ADP-009** | Host Integration Layer |
| **ADP-010** | Engineering Inference Engine |
| **ADP-011** | Assistant Shell User Interface (partial — Phase 1 scaffold; embedded tabs Phase 2) |

### Planned ADPs (referenced, no standalone doc yet)

| ID | Topic (as referenced in architecture) |
|----|---------------------------------------|
| **ADP-004** | Natural-language / EKM conversion (planned) |
| **ADP-005** | EKM provenance and metadata semantics (planned) |

### ADRs (0001–0010)

See [Architecture README](../Architecture/README.md) and [ARCHITECTURE_DECISIONS.md](../../ARCHITECTURE_DECISIONS.md) for the full list. Common references:

| ID | Topic |
|----|-------|
| **ADR-0005** | EKM foundation |
| **ADR-0007** | AERF foundation |
| **ADR-0009** | Platform architecture foundation (three-layer model) |
| **ADR-0010** | **AERP** umbrella acronym |

---

## Code packages (`src/`)

| Path | Layer | Purpose |
|------|-------|---------|
| `src/ekm/` | AERP | EKM runtime, validation, CLI |
| `src/reasoning/` | AERP | AERF stage registry, KB loader, circuit family classifier |
| `src/inference/` | AERP | EIE — chat, simulation, AERF dry-run bundles |
| `src/prompts/` | AERP | Prompt templates and builder |
| `src/providers/` | AERP | LLM provider abstraction |
| `src/platform_core/` | AERP | Host-neutral contracts (`DesignSnapshot`) |
| `src/context/` | KiCad host | Schematic parse, datasheet resolver, `ProjectContext` |
| `src/ui/` | KiCad host | wxPython UI panels |

AERP packages **must not** import KiCad parsers, `pcbnew`, or wxPython. See [Platform Architecture](../Architecture/Platform_Architecture.md).

---

## KiCad and electronics (project usage)

| Term | Meaning in this project |
|------|-------------------------|
| **BOM** | Bill of materials — component list from the design. |
| **ERC** | Electrical Rules Check — schematic rule violations. |
| **DRC** | Design Rules Check — PCB layout rule violations. |
| **SUBCKT** | SPICE subcircuit definition; AI-assisted generation is a Tier A/B/C workflow in the simulation panel. |
| **SPICE** / **ngspice** | Circuit simulation; gap-fill and model generation targets ngspice-friendly `.lib` files. |
| **DCBM** | **D**igital **C**ontrol **B**ehavior **M**odel — simulator-independent engineering contract for electrically relevant discrete/digital control behavior (firmware, measured traces, manual spec, etc.). Includes provenance, confidence, and validation metadata. See [ADP-014](../Architecture/ADP-014-Firmware-Aware-Mixed-Domain-Simulation.md). |
| **DCBM producer** | Engineering Engine Provider role that **creates** DCBM from firmware analysis, trace import, manual authoring, HIL capture, etc. |
| **DCBM consumer** | Simulation adapter or engine provider that **consumes** validated DCBM and produces simulator-specific stimuli or runs mixed-domain simulation. |
| **Simulation-scope slice** | Subset of firmware/control behavior included in a DCBM based on simulation objective and electrical relevance analysis (EIE responsibility). |
| **Mixed-domain simulation** | Combined digital control (MCU firmware behavior) and analog circuit simulation. Level 1: static timing; Level 2: behavioral controller; Level 3: firmware co-simulation. |
| **Simulation Coordinator** | Runtime component exchanging data between DCBM/controller models and analog solvers in closed-loop mixed-signal simulation (future). |
| **Netlist** | Connectivity export; used for context collection and gap-fill analysis. |
| **Datasheet tier A / B / C** | SUBCKT evidence tiers: datasheet-backed, context synthesis, or last-resort inference. See [Prompt Architecture](../Architecture/Prompt_Architecture.md). |

---

## AI and workflow

| Term | Meaning |
|------|---------|
| **LLM** | Large Language Model — cloud or local inference backend. |
| **Approve & Send** | Security pattern: user must explicitly approve before cloud transmission of context or prompts. |
| **general_review** | Ad-hoc schematic Q&A prompt template (`src/prompts/templates/general_review.py`). Not a substitute for full AERF analysis. |
| **Circuit family** | Reusable domain KB (e.g. `blocking_oscillator`) with AERF stages 00–07. Registry: `docs/Engineering_Knowledge/Circuit_Families/families.json`. |
| **Stage 0–7** | Canonical AERF reasoning stages from circuit identification through engineering analysis. See [AERF Stage Index](../Engineering_Knowledge/AERF_Stage_Index.md). |
| **run_aerf_pipeline** | EIE function — sequential stages 0–7 with in-memory `prior_stages`; cloud send only when `approve_send=True`. |
| **write_aerf_stages_to_ekm** | EKM function — map approved stage envelopes to sections; persist only when `approve=True` (CLI `--approve-ekm-writeback`, AERF UI). |
| **EKMViewModel** | View Model layer (`src/ekm/view_model.py`) — validates edits, search/filter, before persistence; used by Engineering Notebook UI. |
| **FieldEditorSpec** | Field-type registry entry (`src/ekm/field_registry.py`) mapping EKM primitives to notebook editors (ADP-003 §9.1). |
| **NotebookRenderer** | wx presentation layer (`src/ui/notebook_renderer.py`) — registry-driven field widgets and collapsible sections. |
| **Engineering Notebook** | Primary human interface to the EKM (ADP-003). CLI: `--ui-notebook` (modal), `--ui-notebook-panel` (non-modal). |
| **send_aerf_stage_prompt** | EIE function — provider call after explicit approval (CLI `--approve-send`, UI `--ui-aerf`). |

---

## External references (out of scope)

| Term | Note |
|------|------|
| **K-AI Plugin** | Community KiCad plugin — UX reference only, not this project's architecture. |
| **KiCad MCP Server** | External MCP approach — different architecture from this repo. |

---

## Maintenance

When introducing a new project acronym or renaming a framework:

1. Add or update an entry in this file first.
2. Link here from other docs instead of re-defining the term inline.
3. Update [Reference README](README.md) if the glossary structure changes.

**Last reviewed:** 2026-07-31
