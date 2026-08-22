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
| Python | 3.9+ (KiCad embeds 3.9.x) | Script execution; Terminal dev may use 3.11+ | `pyproject.toml` |
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

### Local config file

Copy [kicad_ai_config.example.json](kicad_ai_config.example.json) to `~/kicad_ai_config.json` and set `anthropic_api_key` (and optional preferences). Loaded by [`src/utils/config.py`](../../src/utils/config.py). Override path with `KICAD_AI_CONFIG` if needed.

### Secrets handling

- Never commit API keys to the repository
- Use environment variables or `~/kicad_ai_config.json` (gitignored)
- Add any local config files containing secrets to `.gitignore`

## Running the assistant

### External Terminal (recommended)

The primary workflow for UI testing uses **external Python** with `scripts/run_ai_assistant.py`. Context is collected by **parsing project files on disk** (`.kicad_pro`, `.kicad_sch`) — KiCad does **not** need to be open and `pcbnew` is **not** required for this path.

```bash
pip install wxPython   # macOS Terminal; skip if using KiCad Scripting Console
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui-chat
```

Full walkthrough: [Testing With Your KiCad Project](../User_Guides/Testing_With_Your_KiCad_Project.md).

### KiCad Scripting Console

Alternative when you want KiCad's bundled wxPython. KiCad 8–10 embed **Python 3.9.x**; host UI code must avoid PEP 604 unions (`X | Y`) with wx types in runtime-evaluated positions (see `src/ui/wx_typing.py`).

1. Open your project in **KiCad PCB Editor** (`pcbnew`)
2. Select **Tools > Scripting Console**
3. In the **Shell** pane (top, `>>>` prompt — not the History tab), run:

```python
import sys; sys.path.insert(0, "/absolute/path/to/KiCad_AI_Integration/src"); from ui.launcher import show_assistant_shell; show_assistant_shell()
```

The Assistant auto-parents to the open **PcbFrame** / **SchematicFrame** in normal windowed mode. When the PCB editor has a **saved** board open, `show_assistant_shell()` with no path auto-selects the matching `.kicad_pro` beside the `.kicad_pcb`. **macOS full screen** is different: separate windows (Assistant, KiPython) cannot overlay the PCB editor — exit full screen (**Control+Command+F**) or launch from **Terminal** with `--ui`.

Or load the CLI script:

```python
exec(open("/absolute/path/to/KiCad_AI_Integration/scripts/run_ai_assistant.py").read())
main_ui_launcher("/absolute/path/to/project.kicad_pro")
```

On macOS, Terminal launch is often more reliable than Scripting Console paste/focus.

### KiCad ActionPlugin (Phase 2)

Install the plugin package so **Tools → External Plugins → KiCad AI Assistant** opens the unified shell from the PCB Editor.

**Find your plugins folder** (paths vary by OS and KiCad settings). In **PCB Editor → Tools → Scripting Console**:

```python
import pcbnew
print(pcbnew.PLUGIN_DIRECTORIES_SEARCH)
```

Typical locations:

| OS | Common user plugins path |
|----|--------------------------|
| macOS | `~/Documents/KiCad/<version>/scripting/plugins/` |
| macOS (alternate) | `~/Library/Preferences/kicad/<version>/scripting/plugins/` |
| Linux | `~/.config/kicad/<version>/scripting/plugins/` |

**Development symlink** (use the path from `PLUGIN_DIRECTORIES_SEARCH`):

```bash
PLUGIN_DIR="$HOME/Documents/KiCad/10.0/scripting/plugins"   # adjust version/path
mkdir -p "$PLUGIN_DIR"
ln -sfn "$(pwd)/src/plugin/kicad_ai_assistant_plugin.py" "$PLUGIN_DIR/kicad_ai_assistant.py"
```

Use a **single `.py` file symlink** (recommended). KiCad loads `scripting/plugins/*.py` directly; a package directory is optional but less reliable on some setups.

Restart KiCad PCB Editor after installing. The plugin opens a **non-modal** Assistant frame parented to the editor (same shell as `--ui`). Set `KICAD_AI_SRC` to your repo `src/` directory only if the symlink is broken or the repo moved.

### Unit tests (no KiCad)

Unit and integration tests run outside KiCad using file-based fixtures and mocked providers. See [05_Testing.md](05_Testing.md) and [Master Task List](../../tasks/MASTER_TASK_LIST.md).

## IDE configuration

- **Cursor / VS Code:** Open the repository root; use Python extension for `src/` development
- **KiCad Scripting Console:** Use for integration testing with live board data
- **AI-assisted development:** See [AI Engineering Handbook](../AI/README.md) for repository and in-KiCad AI policies

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
- [Testing With Your KiCad Project](../User_Guides/Testing_With_Your_KiCad_Project.md)
