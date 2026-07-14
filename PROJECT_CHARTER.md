# Project Charter

[Home](README.md) · [Project Index](PROJECT_INDEX.md)

> **Status:** Approved
> **Owner:** Project maintainers
> **Applies To:** KiCad AI Integration
> **Last Reviewed:** 2026-07-14
> **Review Frequency:** Annual
> **Authoritative:** Yes

## Mission

Integrate modern Large Language Models directly into the KiCad electronic design environment so AI acts as an experienced engineering assistant throughout the entire design process — with automatic project context rather than manual copy-and-paste workflows.

## Goals

- Integrate AI directly into KiCad
- Automatically gather engineering context (schematics, PCB, netlists, BOM, ERC/DRC)
- Minimize manual copy-and-paste and prompt engineering requirements
- Support iterative engineering conversations
- Provide meaningful circuit analysis and design review
- Keep the architecture provider-independent
- Maintain compatibility with future AI models
- Maintain strong, navigable documentation (EDF adoption)

## Non-Goals

- Replacing the engineer or automating design decisions without human oversight
- Transmitting project data to cloud providers without explicit user approval
- Supporting every AI provider in the initial release
- Building a generic chatbot disconnected from KiCad project context

## Scope

### In Scope

- Python script runnable inside KiCad (Phase 1)
- Context collection from active schematic, PCB, and project metadata
- Prompt construction and Claude Sonnet 3.5 integration (initial provider)
- Provider abstraction layer for future multi-provider support
- Native KiCad plugin with dockable chat (Phase 2)
- Advanced design review capabilities (Phase 3)
- Open-source distribution with contributor documentation

### Out of Scope

- KiCad core modifications
- Automated fabrication or ordering workflows
- Proprietary cloud hosting of user projects
- Support for EDA tools other than KiCad

## Stakeholders

| Role | Responsibility |
|------|----------------|
| Project maintainers | Architecture, code quality, releases |
| KiCad users / contributors | Feature requests, testing, documentation |
| Electronics engineers | Primary end users |
| AI provider ecosystem | External API dependencies (Anthropic, others) |

## Constraints

- **Technical:** Must run within KiCad's embedded Python environment (`pcbnew`, `wxPython`)
- **Security:** API keys never hardcoded; user controls what data is sent to cloud providers
- **Compatibility:** Target KiCad 8+; provider interface must support future models
- **Legal:** License to be determined
- **Documentation:** EDF canonical structure under `docs/`

## Related Documents

- [Project Index](PROJECT_INDEX.md)
- [Software Architecture](docs/Architecture/KiCad_AI_Integration_Software_Architecture.md)
- [Master Task List](tasks/MASTER_TASK_LIST.md)
- [Architecture Decisions](ARCHITECTURE_DECISIONS.md)
