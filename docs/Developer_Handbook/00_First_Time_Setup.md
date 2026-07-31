# First-Time Setup

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Developer Handbook](README.md) › First-Time Setup

## Purpose

Entry point for new contributors setting up a local development environment for KiCad AI Integration. This guide links to authoritative setup documents and KiCad-specific integration guides.

## Prerequisites

- KiCad 8 or later installed
- Poppler utilities (`pdftoppm`) for optional schematic image export at 600 DPI
- An Anthropic API key for Claude Sonnet 3.5 (Phase 1 provider)
- Git for repository access
- A code editor (Cursor or VS Code recommended for AI-assisted development)

### Install Poppler for schematic image export

Optional schematic image context requires `pdftoppm` from Poppler:

- **macOS:** `brew install poppler`
- **Linux:** `apt install poppler-utils` or equivalent
- **Windows:** Install Poppler for Windows and ensure `pdftoppm` is on `PATH`

See [ADR-0004](../Architecture/ADRs/ADR-0004-Optional-Multimodal-Schematic-Context.md).

## Setup checklist

1. **Install KiCad** → [Development Environment](./01_Development_Environment.md#prerequisites) · [[01_Development_Environment#Prerequisites|Prerequisites]]
2. **Clone the repository** → [Repository setup](./01_Development_Environment.md#repository-setup) · [[01_Development_Environment#Repository setup|Repository setup]]
3. **Configure API key** → [Environment variables](./01_Development_Environment.md#environment-variables) · [[01_Development_Environment#Environment variables|Environment variables]]
4. **Review architecture** → [Software Architecture](../Architecture/KiCad_AI_Integration_Software_Architecture.md)
5. **Read integration guides** → [Developer Handbook](README.md)
6. **Check implementation status** → [Master Task List](../../tasks/MASTER_TASK_LIST.md)
7. **AI development rules** → [AI Development](./02_AI_Development.md) · [[02_AI_Development|AI Development]]
8. **Testing strategy** → [Testing](./05_Testing.md) · [[05_Testing|Testing]]
9. **IDE and AI tooling** → [IDE configuration](./01_Development_Environment.md#ide-configuration) · [[01_Development_Environment#IDE configuration|IDE configuration]]
10. **Test with your KiCad project** → [Testing With Your KiCad Project](../User_Guides/Testing_With_Your_KiCad_Project.md) · [E2E Full Flow](./07_E2E_Full_Flow.md)

## Integration guides

After setup, review these guides for KiCad Python integration patterns:

- [KiCad Python API Scripting](Guide-KiCad_Python_API_Custom_AI_Scripting.md)
- [Programmatic AI Analysis](Guide-Programmatic_AI_Analysis.md)
- [In-KiCad Claude Chat Integration](Guide-In_KiCad_Claude_Chat_Integration.md)

## When something fails

→ [Troubleshooting](./01_Development_Environment.md#troubleshooting) · [[01_Development_Environment#Troubleshooting|Troubleshooting]]

## Parent

- [Developer Handbook](README.md)

## Related Documents

- [Project Index](../../PROJECT_INDEX.md)
- [Software Architecture](../Architecture/KiCad_AI_Integration_Software_Architecture.md)
