# Simulation and SUBCKT

[Home](../../README.md) · [User Guides](README.md) · Simulation and SUBCKT

## Overview

The **Simulation** tab finds parts missing ngspice models or KiCad 9 simulation hookup, applies **built-in models** for passives, and can **generate SUBCKT** libraries for custom parts using AI plus datasheets.

**Rationale:** KiCad Simulator needs `Sim.Device`, `Spice_Model`, and `.lib` files. This tab bridges schematic symbols and runnable netlists.

## Who this is for

Engineers preparing designs for **KiCad Simulator** or external ngspice.

## Before you begin

- **Refresh context**
- Datasheets attached for custom parts ([03 — Datasheets](03_Datasheets.md))
- Anthropic API key for **Generate SUBCKT…**

## How to open it

- **Ctrl+3** or **Simulation** tab
- CLI: `--ui-simulation`

---

## UI reference

### Sub-tabs

| Tab | Content |
|-----|---------|
| **Missing models** | Parts with simulation gaps |
| **All required** | Full list including already-hooked parts |

### Columns

Value, Refs, Gap type, Tier (A/B/C), PDF status, Spice_Model, Sim.Device

### Buttons

| Button | Purpose |
|--------|---------|
| **Apply built-in models…** | Bulk write R/C/L/diode/battery Sim.* fields for eligible parts |
| **Generate SUBCKT…** | AI draft `.lib` for selected custom part (Tier A/B/C) |
| **Apply simulation model…** | Write Spice_* / Sim.Device for selected part to schematic |
| **Refresh** | Re-scan gaps from project files |

### Status area

Multiline read-only log of last operation.

---

## Step-by-step workflow

### 1. Apply passives

1. **Refresh context** → open **Simulation**.
2. Review **Missing models**.
3. Click **Apply built-in models…** → confirm.
4. **Reload schematic in KiCad** (File → Revert or reopen) to see property changes.

### 2. Custom part SUBCKT

1. Ensure datasheet PDF exists for the part Value.
2. Select row on **Missing models**.
3. **Generate SUBCKT…** → wait for AI draft in status/output.
4. Review advisory text; fix `.lib` manually if needed.
5. **Apply simulation model…** → confirm write to schematic.
6. Reload schematic in KiCad.

### 3. Verify in KiCad Simulator

Open schematic → **Inspect → Simulator** → run transient/AC as appropriate.

---

## What gets saved

| Location | Content |
|----------|---------|
| Schematic `.kicad_sch` | `Sim.Device`, `Spice_Model`, `Spice_Lib`, etc. |
| Project `*.lib` / library paths | Generated SUBCKT files (per generation result) |

---

## Troubleshooting

### Generate SUBCKT fails

Attach datasheet first; check API key; read gap **Tier** — Tier C may need manual modeling.

### Changes not visible in KiCad

Schematic was modified on disk — **reload/revert** schematic in editor.

### Part on All required but not Missing

Already has Sim.Device=SUBCKT hookup — may only need `.lib` file on disk.

---

## Related documents

- [Custom Trifilar Coil Simulation Setup](Custom_Trifilar_Coil_Simulation_Setup.md)
- [Workflow: Simulation Readiness](Workflows/Simulation_Readiness.md)

## Parent

- [User Guides](README.md)
