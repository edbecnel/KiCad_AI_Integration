# Step-by-step guides
[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [User Guides](README.md) › Step-by-step guides


[Home](../../README.md) · [User Guides](README.md) · Step-by-step guides

## Overview

**Step-by-step guides** are multi-tab workflow playbooks — end-to-end walkthroughs that take you across several Assistant tabs in order. Use them when you have a clear goal (build EKM, review and route a PCB, prepare for simulation) and want numbered steps from start to finish.

For a **single tab**, open that tab's guide (Ctrl+1 … Ctrl+7 or **?** on the tab) and scroll to **Step-by-step workflow** — shorter, tab-focused instructions.

---

## Choose your path

| Your goal | Playbook |
|-----------|----------|
| **New project → curated engineering knowledge (EKM)** | [New Project to EKM](Workflows/New_Project_to_EKM.md) |
| **PCB layout review and autorouting** | [PCB Layout Review and Route](Workflows/PCB_Layout_Review_and_Route.md) |
| **Simulation readiness (SUBCKT, ngspice gaps)** | [Simulation Readiness](Workflows/Simulation_Readiness.md) |

---

## Playbooks

### [New Project to EKM](Workflows/New_Project_to_EKM.md)

Datasheets → AERF stages 0–7 → Write to EKM → verify in Engineering Notebook.

**Tabs used:** Datasheets (Ctrl+2), AERF (Ctrl+4), Notebook (Ctrl+5).

### [PCB Layout Review and Route](Workflows/PCB_Layout_Review_and_Route.md)

Design audits → Freerouting autoroute → checkpoint accept/reject → post-route review.

**Tabs used:** Audits (Ctrl+6), Routing (Ctrl+7).

### [Simulation Readiness](Workflows/Simulation_Readiness.md)

Resolve datasheets → SUBCKT gap scan → spice write-back → KiCad Simulator.

**Tabs used:** Datasheets (Ctrl+2), Simulation (Ctrl+3).

---

## Before you start any playbook

1. Complete [Getting Started](00_Getting_Started.md) (plugin install, API key).
2. Open the Assistant shell and **Refresh context** for your `.kicad_pro`.
3. Save your KiCad project on disk before refreshing — context is read from saved files.

---

## Related

- [User Guides hub](README.md) — full index
- [Assistant Shell](01_Assistant_Shell.md) — tabs, shortcuts, shared header
- Per-tab **Step-by-step workflow** sections in guides 02–08