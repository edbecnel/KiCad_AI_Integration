# Project Index

[Home](README.md) · [Project Charter](PROJECT_CHARTER.md)

> **Navigation hub:** Begin with the project [README](README.md), then use this index to locate authoritative documentation.

## Purpose

This is the primary documentation hub for humans and AI assistants working on KiCad AI Integration.

## Project Status

| Item | Status |
|------|--------|
| Phase | Planning / Initial Development |
| Code | Scaffold only — no `src/` implementation yet |
| Documentation framework | EDF Phase 3 — ADRs and architecture stubs complete |
| License | To be determined |

## Core Documents

- [Project Charter](PROJECT_CHARTER.md)
- [Architecture Decisions](ARCHITECTURE_DECISIONS.md)
- [Master Task List](tasks/MASTER_TASK_LIST.md)
- [Engineering Documentation Framework](ENGINEERING_DOCUMENTATION_FRAMEWORK.md)
- [Changelog](CHANGELOG.md)

## Documentation Domains

### Architecture

- [Architecture](docs/Architecture/README.md)
- [Software Architecture](docs/Architecture/KiCad_AI_Integration_Software_Architecture.md)
- [Prompt Architecture](docs/Architecture/Prompt_Architecture.md)
- [AI Provider Interface](docs/Architecture/AI_Provider_Interface.md)
- [Roadmap](docs/Architecture/Roadmap.md)
- [ADR-0001: KiCad 8+ Minimum Version](docs/Architecture/ADRs/ADR-0001-KiCad-8-Minimum-Version.md)
- [ADR-0002: Provider Abstraction Layer](docs/Architecture/ADRs/ADR-0002-Provider-Abstraction-Layer.md)
- [ADR-0003: Stateless Phase 1 Context Model](docs/Architecture/ADRs/ADR-0003-Stateless-Phase-1-Context-Model.md)
- [ADR-0004: Optional Multimodal Schematic Context](docs/Architecture/ADRs/ADR-0004-Optional-Multimodal-Schematic-Context.md)

### Specifications

- [Specifications](docs/Specifications/README.md)
- [Netlist Gap Fill](docs/Specifications/Netlist_Gap_Fill.md)

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
- [KiCad Python API Scripting Guide](docs/Developer_Handbook/Guide-KiCad_Python_API_Custom_AI_Scripting.md)
- [Programmatic AI Analysis Guide](docs/Developer_Handbook/Guide-Programmatic_AI_Analysis.md)
- [In-KiCad Claude Chat Integration Guide](docs/Developer_Handbook/Guide-In_KiCad_Claude_Chat_Integration.md)

### Reference

- [Reference](docs/Reference/README.md)
- [AI Tools for Advanced Circuit Analysis](docs/Reference/AI_Tools_for_Advanced_Circuit_Analysis.md)

### Other Domains

- [Development](docs/Development/README.md)
- [Specifications](docs/Specifications/README.md)
- [API](docs/API/README.md)
- [Database](docs/Database/README.md)
- [Deployment](docs/Deployment/README.md)
- [User Guides](docs/User_Guides/README.md)
- [Templates](docs/Templates/README.md)

## Current Priorities

1. Complete Phase 1 Python script MVP (context extraction, prompt builder, Claude provider)
2. Resolve project license
3. Begin `src/` implementation per [Master Task List](tasks/MASTER_TASK_LIST.md)

## AI Context

AI assistants should begin here, follow links to authoritative documents, and avoid inventing project facts. The primary architecture document is [Software Architecture](docs/Architecture/KiCad_AI_Integration_Software_Architecture.md). Architecture decisions are in [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md). AI engineering policy is in [AI Engineering Handbook](docs/AI/README.md). Implementation tracking is in [Master Task List](tasks/MASTER_TASK_LIST.md).

## Last Reviewed

2026-07-14
