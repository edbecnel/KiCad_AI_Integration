# Platform Architecture

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Architecture](README.md) › Platform Architecture

> **Status:** Accepted
> **Owner:** Project maintainers
> **Applies To:** AI-assisted Electrical Engineering Reasoning Platform
> **Authoritative:** Yes
> **Ratified by:** [ADR-0009](ADRs/ADR-0009-Platform-Architecture-Foundation.md)

## Purpose

This document defines the **AI-assisted Electrical Engineering Reasoning Platform** — the product vision and architectural layering that KiCad AI Integration implements as its first host integration.

The platform is not a KiCad plugin. KiCad is the **first host application and reference implementation**. The host-agnostic framework stack is **AERP** (**A**I-assisted **E**ngineering **R**easoning **P**latform) — EKM, AERF, EIE, prompts, providers, and related components designed to operate independently of any schematic editor, simulation package, user interface, or large language model. See [ADR-0010](ADRs/ADR-0010-AERP-Platform-Umbrella-Acronym.md).

For acronym and terminology definitions, see the authoritative [Glossary and Acronyms](../Reference/Glossary.md).

Existing ADRs, ADPs, and KiCad-centric documents remain authoritative. This document **extends** them with a platform lens; it does not replace them.

---

## Three-Layer Model

```
AI-assisted Electrical Engineering Reasoning Platform
    ├── AERP (host-agnostic framework stack)
    │       EKM, AERF, EIE, Prompt Architecture, AI Provider Layer,
    │       Artifact Library, Engineering Knowledge Libraries,
    │       Conversation Manager (planned), Simulation Abstraction (planned)
    └── Host Integrations
            └── KiCad AI Integration (first reference host)
                    └── Existing KiCad-centric documentation and code
```

| Layer | Role | Examples |
|-------|------|----------|
| **Platform** | Vision, authority boundaries, cross-host contracts | This document, [ADR-0009](ADRs/ADR-0009-Platform-Architecture-Foundation.md) |
| **AERP** | Host-agnostic framework stack | [ADR-0010](ADRs/ADR-0010-AERP-Platform-Umbrella-Acronym.md); EKM, AERF, EIE — see [Platform Frameworks](#platform-frameworks) |
| **Host Integrations** | Editor- or environment-specific adapters | [ADP-009](ADP-009-Host-Integration-Layer.md), [KiCad Software Architecture](KiCad_AI_Integration_Software_Architecture.md) |

---

## Platform Frameworks (AERP)

**AERP** is the umbrella acronym for this layer. **AERF** is one framework within AERP, not a synonym for the whole stack.

| Framework | What it defines | Primary references | Implementation |
|-----------|-----------------|-------------------|----------------|
| **Engineering Knowledge Model (EKM)** | Canonical authored engineering knowledge | [ADP-001](ADP-001-Engineering-Knowledge-Model-Foundation.md), [ADP-002](ADP-002-EKM-Schema-and-Persistence.md), [ADR-0005](ADRs/ADR-0005-EKM-Foundation.md) | `src/ekm/` (implemented) |
| **AERF** | *What* to reason about: stages 0–7, circuit-family overlays, methodology | [ADP-008](ADP-008-AI-Engineering-Reasoning-Framework.md), [ADR-0007](ADRs/ADR-0007-AERF-Foundation.md) | `src/reasoning/` (stage registry, KB loader, classifier) |
| **Engineering Inference Engine (EIE)** | *How* reasoning runs: orchestration, prompt assembly, provider invocation | [ADP-010](ADP-010-Engineering-Inference-Engine.md) | `src/inference/` (chat, simulation, AERF dry-run bundles) |
| **Prompt Architecture** | How design context becomes structured prompts | [Prompt_Architecture.md](Prompt_Architecture.md) | `src/prompts/` (general review, SUBCKT, AERF stage templates) |
| **AI Provider Layer** | LLM vendor abstraction | [AI_Provider_Interface.md](AI_Provider_Interface.md), [ADR-0002](ADRs/ADR-0002-Provider-Abstraction-Layer.md) | `src/providers/` |
| **Artifact Library** | Content-addressed datasheets, SPICE libs, exports | [Netlist Gap Fill](../Specifications/Netlist_Gap_Fill.md) | `src/context/artifacts/` |
| **Engineering Knowledge Libraries** | Circuit-family reference content | [Engineering Knowledge](../Engineering_Knowledge/README.md) | `docs/Engineering_Knowledge/` |
| **Conversation Manager** | Raw multi-turn transcripts (input, not canonical knowledge) | Software Architecture Component 5 | Deferred Phase 2+ |
| **Simulation Abstraction** | Validation hooks independent of ngspice/KiCad sim | ADP-006 (planned) | Deferred |

### AERF vs EIE

**AERF is a framework within AERP, not AERP itself.**

- **AERF** defines the staged engineering reasoning ontology, acceptance criteria, and circuit-family knowledge overlays.
- **EIE** is the runtime that executes AERF stages, merges `DesignSnapshot` + EKM + KB excerpts, invokes the prompt builder and AI provider layer, handles simulation hooks, and gates EKM write-back.

---

## Authority Boundaries

These boundaries are defined in [ADP-001 §16](ADP-001-Engineering-Knowledge-Model-Foundation.md) and apply platform-wide. Host integrations own connectivity and extraction; frameworks own reasoning and knowledge.

| Domain | Authoritative source |
|--------|---------------------|
| Electrical connectivity | Host design files (KiCad schematic / netlist for the reference host) |
| Extracted design facts | `DesignSnapshot` (KiCad: `ProjectContext`) |
| Engineering intent, rationale, assumptions, curated decisions | EKM |
| Chat transcript and API turn context | Conversation Manager |
| Reusable circuit ontology | Circuit Family KB (`docs/Engineering_Knowledge/`) |
| Transient per-analysis reasoning | AERF stage outputs (via EIE) |
| Datasheets, SPICE libs, simulation exports | Artifact library |
| LLM vendors | AI Provider Layer |

---

## Host Integration Layer

Each host implements the contract in [ADP-009](ADP-009-Host-Integration-Layer.md):

1. **Context collection** → `DesignSnapshot`
2. **Optional UI shell** (dialogs, dockable panels, web UI, CLI)
3. **Project artifact root** (KiCad: `<project>/kicad_ai/`)
4. **Object linking** for EKM references (KiCad: `KiCadLink`)
5. **Optional write-back** to host design files

KiCad AI Integration is documented in [KiCad Software Architecture](KiCad_AI_Integration_Software_Architecture.md).

---

## Source Code Logical Layers

Physical directory moves are deferred until a second host is actively developed ([ADR-0009](ADRs/ADR-0009-Platform-Architecture-Foundation.md)). Current mapping:

```
src/
  providers/          → AERP: AI Provider Layer
  prompts/            → AERP: Prompt Architecture
  platform_core/      → AERP: shared contracts (DesignSnapshot)
  ekm/                → AERP: EKM runtime
  reasoning/          → AERP: AERF stage registry and KB loaders
  inference/          → AERP: EIE orchestrator (chat, simulation, AERF dry-run)
  context/artifacts/  → AERP: Artifact Library
  context/model.py    → Shared: DesignSnapshot (KiCad-shaped today)
  context/*parse*     → Host (KiCad): collection and write-back
  ui/                 → Host (KiCad): UI shell
  plugin/             → Host (KiCad): native integration (planned)
```

### Import boundaries

Platform modules (AERP: `providers/`, `prompts/`, `platform_core/`, `ekm/`, `reasoning/`, `inference/`) **must not** import KiCad-specific parsers (`context/schematic_*`, `context/pcb_*`), wxPython UI, or `pcbnew`. Host modules may import platform modules. See [Developer Handbook](../Developer_Handbook/README.md).

---

## Future Host Applications

| Host type | Integration pattern |
|-----------|---------------------|
| **KiCad** (current) | File parse + `kicad-cli` + wx UI + `kicad_ai/` artifacts |
| **Standalone desktop** | Import netlist/schematic files → `DesignSnapshot`; native UI |
| **Web application** | Upload design files; server-side EIE; browser UI |
| **CLI tool** | SPICE/netlist/JSON input → `DesignSnapshot`; stdout/JSON output |
| **Educational** | Simplified `DesignSnapshot` + AERF subset; EKM as lesson workbook |
| **Laboratory software** | Measurements as artifacts; EKM `measurement` fields |
| **Other EDA tools** | New collector + host link type; reuse platform frameworks |

Physical reorganization into `src/hosts/kicad/` is deferred until a second host integration is in active development.

---

## Related Documents

| Topic | Document |
|-------|----------|
| Host integration contract | [ADP-009](ADP-009-Host-Integration-Layer.md) |
| Inference engine | [ADP-010](ADP-010-Engineering-Inference-Engine.md) |
| KiCad host implementation | [KiCad Software Architecture](KiCad_AI_Integration_Software_Architecture.md) |
| Platform decision | [ADR-0009](ADRs/ADR-0009-Platform-Architecture-Foundation.md) |
| Project vision | [Project Overview](../../PROJECT_OVERVIEW.md) |

## Parent

- [Architecture](README.md)
