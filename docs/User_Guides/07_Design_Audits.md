# Design Audits
[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [User Guides](README.md) › Design Audits


[Home](../../README.md) · [User Guides](README.md) · Design Audits

## Overview

The **Audits** tab runs **one-click engineering reviews** with structured findings. Each audit requires approval before sending context to the provider. Reports are saved as JSON under `kicad_ai/reviews/`.

**Rationale:** Faster than crafting a Chat prompt for standard review types (schematic review, PCB layout, DRC explanation). Output uses a consistent **ReviewReport** schema.

## Who this is for

Engineers who want quick structured feedback on schematic, PCB, or domain-specific concerns.

## Before you begin

- **Refresh context**
- API key configured
- For DRC audit: DRC report available (`kicad-cli pcb drc` or existing report files)

## How to open it

- **Ctrl+6** or **Audits** tab
- CLI: `--audit-schematic` or `--audit-pcb` (opens Audits tab)

---

## UI reference

| Button | Purpose |
|--------|---------|
| **Schematic review** | General schematic engineering review |
| **PCB layout review** | Layout, placement, routing quality |
| **Explain DRC** | Interpret DRC violations in context |
| **Isolation / clearance** | Creepage/clearance and isolation focus |
| **Circuit explanation** | Explain circuit operation from context |
| **Findings** panel | Narrative + structured severity lines (read-only) |
| Status line | Ready / busy / error state |

---

## Step-by-step workflow

1. **Refresh context** in shell header.
2. Open **Audits** (Ctrl+6).
3. Click the audit type you need.
4. Confirm **Approve transmission** dialog.
5. Wait for completion — findings appear in the panel.
6. Open saved report under `<project>/kicad_ai/reviews/` if needed.

**Expected result:** Findings list with severity/category; status shows report path or completion.

---

## What gets saved

| Path | Content |
|------|---------|
| `<project>/kicad_ai/reviews/*.json` | ReviewReport JSON per audit run |

---

## Troubleshooting

### Audit buttons disabled

Another audit is running — wait for completion.

### DRC audit weak or empty

Run PCB DRC in KiCad or ensure `kicad-cli` is configured; **Refresh context**.

### Provider error

Check API key and network; see [11 — Troubleshooting](11_Troubleshooting.md).

---

## Related documents

- [02 — Chat](02_Chat.md) — ad-hoc questions
- [08 — PCB Routing](08_PCB_Routing.md) — post-route review
- [Workflow: PCB Review and Route](Workflows/PCB_Layout_Review_and_Route.md)

## Parent

- [User Guides](README.md)