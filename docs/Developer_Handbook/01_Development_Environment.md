# Development Environment

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Developer Handbook](README.md) › Development Environment

## Purpose

Canonical reference for local development environment setup, configuration, and troubleshooting for KiCad AI Integration.

New contributors should follow [00_First_Time_Setup.md](./00_First_Time_Setup.md) first.

## Prerequisites

### Required software

| Tool | Minimum version | Purpose | Install reference |
|------|-----------------|---------|-------------------|
| KiCad | 8.0+ | EDA platform and embedded Python runtime | [kicad.org](https://www.kicad.org/) |
| Git | 2.x | Version control | System package manager |
| Python | 3.x (bundled with KiCad) | Script execution inside KiCad | Included with KiCad |
| wxPython | Bundled with KiCad | In-KiCad UI dialogs | Included with KiCad |

### KiCad Python API

KiCad exposes the `pcbnew` module for PCB data access and schematic APIs for schematic data. Scripts run inside KiCad's embedded Python interpreter via **Tools > Scripting Console** in the PCB Editor.

Confirm availability before development:

- `import pcbnew` succeeds in the KiCad Scripting Console
- `wx` (wxPython) is available for UI components
- Schematic access APIs are available for your target KiCad version

## Repository setup

### Clone and initialize

```bash
git clone https://github.com/edbecnel/KiCad_AI_Integration.git
cd KiCad_AI_Integration
```

### Environment variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Yes (Phase 1) | Anthropic API key for Claude Sonnet 3.5 | `sk-ant-...` |

Set in your shell profile or export before running scripts inside KiCad:

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Secrets handling

- Never commit API keys to the repository
- Use environment variables as the primary credential source
- Optional local config file support is planned (see [Master Task List](../../tasks/MASTER_TASK_LIST.md))
- Add any local config files containing secrets to `.gitignore`

## Running code inside KiCad

### Scripting Console

1. Open your project in **KiCad PCB Editor** (`pcbnew`)
2. Select **Tools > Scripting Console**
3. Run project scripts from `scripts/` (once implemented)

### External execution

Some unit tests can run outside KiCad using mocked `pcbnew` objects and file-based fixtures. See [Master Task List](../../tasks/MASTER_TASK_LIST.md) for the testing strategy.

## IDE configuration

- **Cursor / VS Code:** Open the repository root; use Python extension for `src/` development
- **KiCad Scripting Console:** Use for integration testing with live board data
- **AI-assisted development:** See [AI domain — Phase 2](../AI/README.md) for the modular AI Engineering Handbook

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| `import pcbnew` fails | Run script inside KiCad, not system Python |
| wxPython dialog errors | Confirm wxPython is available in KiCad's Python |
| API authentication failure | Verify `ANTHROPIC_API_KEY` is set and valid |
| Schematic API unavailable | Confirm KiCad version supports schematic scripting for your target |

## Parent

- [Developer Handbook](README.md)

## Related Documents

- [KiCad Python API Scripting Guide](Guide-KiCad_Python_API_Custom_AI_Scripting.md)
- [Programmatic AI Analysis Guide](Guide-Programmatic_AI_Analysis.md)
- [In-KiCad Claude Chat Integration Guide](Guide-In_KiCad_Claude_Chat_Integration.md)
