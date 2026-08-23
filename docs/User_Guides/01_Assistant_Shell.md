# Assistant Shell

[Home](../../README.md) · [User Guides](README.md) · Assistant Shell

## Overview

The **Assistant shell** is the unified KiCad AI window: one project header, one **Refresh context** action, and seven embedded feature tabs. All tabs share the same collected project context so you do not re-scan the project separately for Chat, Datasheets, AERF, and the rest.

## Who this is for

Anyone using `--ui`, the KiCad ActionPlugin, or `show_assistant_shell()` from the scripting console.

## Before you begin

- Complete [Getting Started](00_Getting_Started.md)
- A saved KiCad project (`.kicad_pro`)

## How to open it

| Method | Action |
|--------|--------|
| **KiCad plugin** | PCB Editor → **Tools → External Plugins → KiCad AI Assistant** |
| **CLI** | `python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui` |
| **Deep link** | `--ui-chat`, `--ui-datasheets`, `--ui-simulation`, `--ui-aerf`, `--ui-notebook`, `--audit-schematic`, `--audit-pcb`, `--ui-routing` |

---

## Shared header controls

| Control | Purpose |
|---------|---------|
| **Project** | Path to `.kicad_pro`. Editable; use **Browse…** to pick another project |
| **Browse…** | File picker for `.kicad_pro` |
| **Refresh context** | Re-reads schematic, PCB, BOM, netlist, datasheets from disk; updates summary and all tabs |
| **Settings…** | Provider profile (Claude / Ollama, API key, models) → saves `~/kicad_ai_config.json` |
| **Help** | Opens the in-app **User Guide** (rendered markdown). On the active tab, opens that tab's guide. Use the **Step-by-step guides** sidebar group for multi-tab workflow playbooks |

### Context summary panel

Read-only text below the header. Typical contents:

- Project name and schematic file list
- Symbol count, datasheet resolution status
- Netlist line count, estimated prompt tokens
- Simulation gap summary (when applicable)
- Notice if required datasheets are missing

**Rationale:** One refresh feeds every tab. Always **Refresh context** after saving schematic or PCB changes on disk.

---

## Feature tabs

| Shortcut | Tab | Guide |
|----------|-----|-------|
| **Ctrl+1** | Chat | [02 — Chat](02_Chat.md) |
| **Ctrl+2** | Datasheets | [03 — Datasheets](03_Datasheets.md) |
| **Ctrl+3** | Simulation | [04 — Simulation](04_Simulation_and_SUBCKT.md) |
| **Ctrl+4** | AERF | [05 — AERF](05_AERF_Staged_Analysis.md) |
| **Ctrl+5** | Notebook | [06 — Engineering Notebook](06_Engineering_Notebook.md) |
| **Ctrl+6** | Audits | [07 — Design Audits](07_Design_Audits.md) |
| **Ctrl+7** | Routing | [08 — PCB Routing](08_PCB_Routing.md) |

Each tab shows a **?** button in the top-right corner to open help for that tab.

### Datasheets tab badge

When required datasheets are missing, the tab label shows **Datasheets (N)** where N is the missing count. Clears when PDFs are resolved.

### Tab loading behavior

Each tab shows a placeholder until **Refresh context** completes. After refresh, the tab loads its feature panel for the current project path. Switching projects requires **Refresh context** (or changing the path and refreshing).

### Last-tab memory

The shell remembers the last active tab per project in `~/kicad_ai_shell_prefs.json` and restores it on next open.

---

## Status bar

Bottom line of the shell. Examples:

- `Select a project and refresh context.` — idle
- `Collecting context…` — refresh in progress
- `Context ready — MyBoard.kicad_pro` — success
- `Context error: …` — path or collection failure

---

## Close and unsaved-work guards

Closing the Assistant window may be blocked when:

- **Notebook** has unsaved EKM edits
- A tab reports a busy operation (long datasheet fetch, audit in progress, routing run)

Confirm discard when prompted.

---

## Step-by-step: typical session

1. Open KiCad PCB Editor with your project saved.
2. Launch **KiCad AI Assistant**.
3. Confirm **Project** path → **Refresh context**.
4. Use tabs as needed (Ctrl+1–7).
5. After schematic edits on disk → **Refresh context** again before Chat or AERF.

---

## Troubleshooting

### Tab shows placeholder after refresh

Check status bar for context errors. Verify `.kicad_pro` path and that schematic files exist.

### Wrong project loaded

Edit **Project** field or **Browse…**, then **Refresh context**.

### Shortcuts do not work

Click inside the Assistant window first; shortcuts are handled when the shell has focus.

---

## Related documents

- [00 — Getting Started](00_Getting_Started.md)
- [Feature Overview](Feature_Overview.md)
- [ADP-011 Assistant Shell UI](../Architecture/ADP-011-Assistant-Shell-UI.md) (architecture)

## Parent

- [User Guides](README.md)
