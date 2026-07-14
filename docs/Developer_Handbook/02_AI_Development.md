# AI Development

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Developer Handbook](README.md) › AI Development

## Purpose

Practical conventions for using AI tools during KiCad AI Integration development. This document complements the authoritative [AI Engineering Handbook](../AI/README.md) with project-specific rules and workflows.

Policy and philosophy live in `docs/AI/`. This handbook section covers day-to-day developer practice.

## When to use it

- Before first AI-assisted commit in this repository
- When working on in-KiCad integration scripts or provider code
- During code review of AI-generated changes
- When deciding what project data may be sent to cloud providers

## Approved tools

| Tool | Use case | Status |
|------|----------|--------|
| Cursor + Composer 2.5 | Repository code, documentation, tests in `src/` | Approved |
| Claude Sonnet 3.5 | In-KiCad circuit analysis via Anthropic API | Approved — Phase 1 provider |
| Ollama (local) | Sensitive schematic drafts, air-gapped workflows | Planned — future provider |

For role definitions, see [AI Roles](../AI/AI_Roles.md) and [AI Decision Matrix](../AI/AI_Decision_Matrix.md).

## Data and privacy rules

### May send to cloud AI — with user approval

- Schematic, PCB, netlist, BOM, ERC/DRC data the user explicitly selects
- Optional high-resolution schematic image (600 DPI PNG via `kicad-cli` + `pdftoppm`) when user enables "Include schematic image"
- User-entered design intent text
- Structured extraction JSON from KiCad project context

### Must not send to cloud AI

- `ANTHROPIC_API_KEY` or any credentials in prompts
- Project data without explicit user approval via the context preview and Approve step
- Data the user has deselected via context inclusion toggles

### Credential handling

- Store `ANTHROPIC_API_KEY` in environment variables only
- Never commit API keys to the repository

See [Security](../AI/Security.md) and [Development Environment](01_Development_Environment.md).

## External dependencies for multimodal context

Schematic image export uses subprocess calls outside KiCad's embedded Python:

| Tool | Purpose | Install |
|------|---------|---------|
| `kicad-cli` | Export schematic to PDF | Bundled with KiCad 8+ |
| `pdftoppm` | Rasterize PDF to PNG at 600 DPI | Poppler — see [First-Time Setup](00_First_Time_Setup.md) |

Set `KICAD_CLI` environment variable if `kicad-cli` is not on `PATH` (common on macOS).

## Providing context to AI

### Repository development — recommended entry points

1. [PROJECT_INDEX.md](../../PROJECT_INDEX.md)
2. [Software Architecture](../Architecture/KiCad_AI_Integration_Software_Architecture.md)
3. Applicable [ADR](../../ARCHITECTURE_DECISIONS.md)
4. [Master Task List](../../tasks/MASTER_TASK_LIST.md) for implementation scope

### In-KiCad integration work

- [KiCad Python API Scripting Guide](Guide-KiCad_Python_API_Custom_AI_Scripting.md)
- [Programmatic AI Analysis Guide](Guide-Programmatic_AI_Analysis.md)
- [In-KiCad Claude Chat Integration Guide](Guide-In_KiCad_Claude_Chat_Integration.md)

## AI-generated code requirements

- Meet the same review and test standards as human-written code
- KiCad Python scripts must be reviewed before running against live projects
- Update documentation when architecture or behavior changes

## Related Documents

- [AI Engineering Handbook](../AI/README.md)
- [05_Testing.md](05_Testing.md)
- [00_First_Time_Setup.md](00_First_Time_Setup.md)

## Parent

- [Developer Handbook](README.md)
