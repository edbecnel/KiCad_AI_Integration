# Troubleshooting

[Home](../../README.md) · [User Guides](README.md) · Troubleshooting

## Overview

Common problems when using the KiCad AI Assistant plugin and Terminal launch paths.

---

## Installation and launch

### Plugin missing from Tools menu

1. Verify plugin path: `pcbnew.PLUGIN_DIRECTORIES_SEARCH` in Scripting Console.
2. Symlink or copy `src/plugin/kicad_ai_assistant` into that folder.
3. Restart KiCad PCB Editor.

### `ImportError` / `cannot import name 'UTC' from 'datetime'`

KiCad uses Python 3.9. Update to a current plugin build; report if error persists after pull.

### Assistant window not visible (macOS full screen)

Exit full screen: **Control+Command+F**. Or launch from Terminal: `python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui`.

### wxPython errors in Terminal

```bash
pip install wxPython
```

KiCad Scripting Console includes wx — plugin path does not need separate install.

---

## Context and project

### 0 symbols / empty summary

- Save schematic in KiCad (**File → Save**).
- Confirm `.kicad_sch` exists beside `.kicad_pro`.
- Verify **Project** path → **Refresh context**.

### Stale schematic after external edits

KiCad does not auto-reload disk changes. **Revert** schematic or reopen project, then **Refresh context**.

### Context error in status bar

Check path is valid `.kicad_pro`; project directory readable.

---

## AI provider

### API key rejected

- Set key in **Settings…** or `~/kicad_ai_config.json`
- Or `export ANTHROPIC_API_KEY=...`
- For Ollama: set `"ai_provider": "ollama"` and start Ollama service

### Timeout / long hangs

Increase `provider_read_timeout_sec` in config. Large schematics produce large prompts.

---

## Datasheets

### Badge (N) won't clear

Attach PDFs for all rows on **Missing** tab; **Refresh context**.

### AI discovery fails

Check API key; enable checkbox; verify network.

---

## Simulation

### SUBCKT generation fails

Attach datasheet first ([03 — Datasheets](03_Datasheets.md)).

### Schematic properties unchanged in editor

Reload schematic after Simulation write-back.

---

## Routing

### Run autoroute disabled

Set `"routing_enabled": true` and `freerouting_jar` in `~/kicad_ai_config.json`. See [08 — PCB Routing](08_PCB_Routing.md).

### Freerouting not installed

Download Freerouting standalone JAR; set full path in config.

---

## UI layout

### Overlapping controls or truncated Chat tab

Reload plugin (restart KiCad or reload from Scripting Console). Ensure latest build.

### Notebook duplicate open questions

Each row is a distinct AERF question — labels show full text after recent updates. Re-run **Write to EKM…** to clean stale entries.

---

## Getting help

- [User Guides hub](README.md)
- [Testing With Your KiCad Project](Testing_With_Your_KiCad_Project.md) — validation checklist
- [GitHub Issues](https://github.com/edbecnel/KiCad_AI_Integration/issues)

## Parent

- [User Guides](README.md)
