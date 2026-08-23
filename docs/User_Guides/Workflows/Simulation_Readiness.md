# Workflow: Simulation Readiness

[Home](../../../README.md) · [User Guides](../README.md) · Workflows

## Overview

Prepare a schematic for **KiCad Simulator** by resolving datasheets, filling simulation gaps, and applying SUBCKT models.

## Prerequisites

- Saved schematic
- ngspice available through KiCad Simulator
- API key for SUBCKT generation (custom parts)

---

## Steps

### 1. Datasheets (Ctrl+2)

1. **Refresh context** → **Datasheets**.
2. Attach PDFs for custom parts (transformers, transistors, etc.).
3. **Refresh context** when complete.

See [03 — Datasheets](../03_Datasheets.md).

### 2. Simulation gaps (Ctrl+3)

1. **Simulation** tab → **Missing models**.
2. **Apply built-in models…** for R/C/L/diodes/batteries.
3. For each custom part: **Generate SUBCKT…** → review → **Apply simulation model…**.
4. **Reload schematic** in KiCad after writes.

See [04 — Simulation](../04_Simulation_and_SUBCKT.md).

### 3. Deep-dive (optional)

For trifilar / custom magnetics, follow [Custom Trifilar Coil Simulation Setup](../Custom_Trifilar_Coil_Simulation_Setup.md).

### 4. Run simulator

KiCad schematic → **Inspect → Simulator** → configure analysis → run.

---

## Expected outcome

- No critical rows on **Missing models** (or only documented exceptions)
- `Sim.Device` / `Spice_Model` fields set on schematic
- Simulator netlist builds without missing model errors

## Parent

- [User Guides](../README.md)
