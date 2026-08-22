# Project Index

[Home](README.md) · [Project Charter](PROJECT_CHARTER.md)

> **Navigation hub:** Begin with the project [README](README.md), then use this index to locate authoritative documentation.

## Purpose

This is the primary documentation hub for humans and AI assistants working on KiCad AI Integration.

## Project Status

| Item | Status |
|------|--------|
| Phase | Post Track C/D — Phase 1 file-based close-out complete; Phase 2 next |
| Code | Full assistant: chat, datasheets, simulation, AERF, notebook, pin connectivity, gap-fill detection, CI (`pytest`) |
| Documentation framework | EDF Phase 3 — ADRs and architecture stubs complete |
| License | MIT — see [LICENSE](LICENSE) |

## Core Documents

- [Project Overview](PROJECT_OVERVIEW.md)
- [Project Charter](PROJECT_CHARTER.md)
- [Platform Architecture](docs/Architecture/Platform_Architecture.md)
- [Architecture Inventory](Architecture_Inventory.md)
- [Handover notes](HANDOVER.md) (session handover index)
- [Example: Bedini Babcock workflow](examples/bedini_babcock/README.md)
- [Master Task List](tasks/MASTER_TASK_LIST.md)
- [Engineering Documentation Framework](ENGINEERING_DOCUMENTATION_FRAMEWORK.md)
- [Glossary and Acronyms](docs/Reference/Glossary.md)
- [Changelog](CHANGELOG.md)

## Documentation Domains

### Architecture

KiCad AI Integration is the **first host integration** of the AI-assisted Electrical Engineering Reasoning Platform. Platform-level architecture is documented separately from KiCad-specific implementation.

- [Platform Architecture](docs/Architecture/Platform_Architecture.md)
- [Architecture](docs/Architecture/README.md)
- [Software Architecture (KiCad Host)](docs/Architecture/KiCad_AI_Integration_Software_Architecture.md)
- [ADP-009: Host Integration Layer](docs/Architecture/ADP-009-Host-Integration-Layer.md)
- [ADP-010: Engineering Inference Engine](docs/Architecture/ADP-010-Engineering-Inference-Engine.md)
- [ADP-011: Assistant Shell User Interface](docs/Architecture/ADP-011-Assistant-Shell-UI.md) (Phase 1 scaffold)
- [Prompt Architecture](docs/Architecture/Prompt_Architecture.md)
- [AI Provider Interface](docs/Architecture/AI_Provider_Interface.md)
- [Roadmap](docs/Architecture/Roadmap.md)
- [ADR-0001: KiCad 8+ Minimum Version](docs/Architecture/ADRs/ADR-0001-KiCad-8-Minimum-Version.md)
- [ADR-0002: Provider Abstraction Layer](docs/Architecture/ADRs/ADR-0002-Provider-Abstraction-Layer.md)
- [ADR-0003: Stateless Phase 1 Context Model](docs/Architecture/ADRs/ADR-0003-Stateless-Phase-1-Context-Model.md)
- [ADR-0004: Optional Multimodal Schematic Context](docs/Architecture/ADRs/ADR-0004-Optional-Multimodal-Schematic-Context.md)
- [ADR-0005: EKM Foundation](docs/Architecture/ADRs/ADR-0005-EKM-Foundation.md)
- [ADR-0006: Engineering Notebook UI](docs/Architecture/ADRs/ADR-0006-Engineering-Notebook-UI.md)
- [ADR-0007: AERF Foundation](docs/Architecture/ADRs/ADR-0007-AERF-Foundation.md)
- [ADR-0008: EKM Schema and Persistence](docs/Architecture/ADRs/ADR-0008-EKM-Schema-and-Persistence.md)
- [ADR-0009: Platform Architecture Foundation](docs/Architecture/ADRs/ADR-0009-Platform-Architecture-Foundation.md)
- [ADR-0010: AERP Platform Umbrella Acronym](docs/Architecture/ADRs/ADR-0010-AERP-Platform-Umbrella-Acronym.md)
- [ADP-008: AI Engineering Reasoning Framework](docs/Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md)
- [ADP-013: Routing Abstraction](docs/Architecture/ADP-013-Routing-Abstraction.md) (draft)

### Engineering Knowledge

- [Engineering Knowledge](docs/Engineering_Knowledge/README.md)
- [AERF Stage Index](docs/Engineering_Knowledge/AERF_Stage_Index.md)
- [Circuit Families](docs/Engineering_Knowledge/Circuit_Families/README.md)

### Specifications

- [Specifications](docs/Specifications/README.md)
- [Netlist Gap Fill](docs/Specifications/Netlist_Gap_Fill.md)
- [Freerouting Integration](docs/Specifications/Freerouting_Integration.md) (draft)

### AI Engineering Handbook

- [AI Engineering Handbook](docs/AI/README.md)
- [AI Philosophy](docs/AI/AI_Philosophy.md)
- [AI Roles](docs/AI/AI_Roles.md)
- [AI Decision Matrix](docs/AI/AI_Decision_Matrix.md)
- [Prompting Guide](docs/AI/Prompting_Guide.md)
- [Context Checklist](docs/AI/Context_Checklist.md)
- [Security](docs/AI/Security.md)
- [Verification](docs/AI/Verification.md)
- [Cost Optimization](docs/AI/Cost_Optimization.md)
- [Repository Workflow](docs/AI/Repository_Workflow.md)
- [AI Governance](docs/AI/Governance.md)

### Governance

- [Governance](docs/Governance/README.md)
- [Governance Overview](docs/Governance/Governance_Overview.md)
- [Document Metadata Standard](docs/Governance/Document_Metadata_Standard.md)
- [Document Lifecycle](docs/Governance/Document_Lifecycle.md)
- [Ownership and Review](docs/Governance/Ownership_and_Review.md)
- [Change Management](docs/Governance/Change_Management.md)
- [Governance Checklist](docs/Governance/Governance_Checklist.md)

### Developer Handbook

- [Developer Handbook](docs/Developer_Handbook/README.md)
- [First-Time Setup](docs/Developer_Handbook/00_First_Time_Setup.md)
- [Development Environment](docs/Developer_Handbook/01_Development_Environment.md)
- [AI Development](docs/Developer_Handbook/02_AI_Development.md)
- [Testing](docs/Developer_Handbook/05_Testing.md)
- [E2E Chat UI](docs/Developer_Handbook/06_E2E_Chat_UI.md)
- [E2E Full Flow](docs/Developer_Handbook/07_E2E_Full_Flow.md)
- [KiCad Python API Scripting Guide](docs/Developer_Handbook/Guide-KiCad_Python_API_Custom_AI_Scripting.md)
- [Programmatic AI Analysis Guide](docs/Developer_Handbook/Guide-Programmatic_AI_Analysis.md)
- [In-KiCad Claude Chat Integration Guide](docs/Developer_Handbook/Guide-In_KiCad_Claude_Chat_Integration.md)

### User Guides

- [User Guides](docs/User_Guides/README.md)
- [Feature Overview](docs/User_Guides/Feature_Overview.md) — KiCad capabilities, platform scope, and how the system works
- [How AERF Works](docs/User_Guides/How_AERF_Works.md) — staged analysis vs Chat and copy-paste workflows
- [Testing With Your KiCad Project](docs/User_Guides/Testing_With_Your_KiCad_Project.md) — validate chat, AERF, and Notebook with your own schematic

### Reference

- [Reference](docs/Reference/README.md)
- [Glossary and Acronyms](docs/Reference/Glossary.md)
- [AI Tools for Advanced Circuit Analysis](docs/Reference/AI_Tools_for_Advanced_Circuit_Analysis.md)

### Other Domains

- [Development](docs/Development/README.md)
- [Specifications](docs/Specifications/README.md)
- [API](docs/API/README.md)
- [Database](docs/Database/README.md)
- [Deployment](docs/Deployment/README.md)
- [Templates](docs/Templates/README.md)

## Current Priorities

**Track C — AERF + EIE depth** (complete; see [Feature Overview](docs/User_Guides/Feature_Overview.md) Part 4):

1. ~~Circuit family classifier from `DesignSnapshot`~~ (done — `src/reasoning/classifier.py`)
2. ~~Per-stage prompt templates (ADP-007)~~ (done — `src/prompts/templates/aerf_stage.py`)
3. ~~Full AERF multi-stage orchestration with approval gating~~ (done — `run_aerf_pipeline`, `--approve-send`, `--ui-aerf`)
4. ~~EKM write-back from approved stage outputs (ADP-007)~~ (done — `src/ekm/aerf_writeback.py`, `--approve-ekm-writeback`, `--ui-aerf` Write to EKM)

**Track D — Engineering Notebook (ADP-003)** (complete):

1. ~~EKM View Model (`src/ekm/view_model.py`)~~ (done)
2. ~~Field-type registry (`src/ekm/field_registry.py`) + all primitive editors~~ (done)
3. ~~Search, collapsible sections, renderer split (`src/ui/notebook_renderer.py`)~~ (done)
4. ~~Non-modal panel + Advanced JSON view (`--ui-notebook-panel`)~~ (done)

**Recommended next:** Phase 2 — embedded Assistant tabs, dockable KiCad plugin, multi-turn chat. See [Master Task List](tasks/MASTER_TASK_LIST.md).

Standing rule: update Feature Overview and [Master Task List](tasks/MASTER_TASK_LIST.md) at each milestone.

**Testing:** [Testing With Your KiCad Project](docs/User_Guides/Testing_With_Your_KiCad_Project.md) — external-script E2E validation (no native plugin required).

## AI Context

AI assistants should begin here, follow links to authoritative documents, and avoid inventing project facts. Terminology and acronyms: [Glossary](docs/Reference/Glossary.md). Scope and capability status: [Feature Overview](docs/User_Guides/Feature_Overview.md). The platform architecture is in [Platform Architecture](docs/Architecture/Platform_Architecture.md). The KiCad host implementation is in [Software Architecture](docs/Architecture/KiCad_AI_Integration_Software_Architecture.md). Architecture decisions are in [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md). AI engineering policy is in [AI Engineering Handbook](docs/AI/README.md). Implementation tracking is in [Master Task List](tasks/MASTER_TASK_LIST.md).

## Last Reviewed

2026-08-07
