# AERF Staged Analysis
[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [User Guides](README.md) › AERF Staged Analysis


[Home](../../README.md) · [User Guides](README.md) · AERF Staged Analysis

## Overview

**AERF** (AI Engineering Reasoning Framework) runs **eight structured stages** (0–7) of circuit analysis. Each stage requires **Approve & Send** before calling the provider. After stage 7, you can **Write to EKM…** to persist approved conclusions in the Engineering Notebook.

**Rationale:** Staged JSON output is reviewable and mappable to EKM sections. Chat is for ad-hoc questions; AERF is for systematic engineering reasoning you want to keep.

## Who this is for

Engineers running formal design analysis who will curate results in the [Notebook](06_Engineering_Notebook.md).

## Before you begin

- **Refresh context**
- API key configured
- Recommended: resolve datasheets ([03 — Datasheets](03_Datasheets.md))
- Read [How AERF Works](How_AERF_Works.md) for stage meanings

## How to open it

- **Ctrl+4** or **AERF** tab
- CLI: `--ui-aerf`

---

## UI reference

| Control | Purpose |
|---------|---------|
| **API key** | Session override (password field) |
| **Circuit family** | AERF family id (e.g. `blocking_oscillator`); loaded from EKM if present |
| **AERF stage (0–7)** | Stage to preview or send |
| **Include schematic image** | Multimodal prompt |
| **Context / prompt preview** | Read-only assembled prompt for current stage |
| **Preview stage prompt** | Rebuild preview without sending |
| **Approve & Send stage** | Confirm and send current stage to provider |
| **Write to EKM…** | Enabled after stage 7 completed — persist to `engineering_knowledge.json` |
| **Stage response** | Provider JSON response for last sent stage |
| Status line | Stage progress and errors |

### Stage summary (user-facing)

| Stage | Focus |
|-------|--------|
| **0** | Circuit identification, topology, family |
| **1–3** | Operation and principles |
| **4** | Component rationale |
| **5–6** | Operating conditions |
| **7** | Engineering analysis, conclusions, recommendations |

---

## Step-by-step workflow

### 1. Run stages

1. **Refresh context**.
2. Set **Circuit family** if not auto-filled.
3. Set stage **0** → **Preview stage prompt** → review.
4. **Approve & Send stage** → confirm.
5. On success, advance through stages **1–7**, repeating preview and approve for each.

**Expected result:** **Stage response** shows structured JSON per stage; completed stages accumulate internally.

### 2. Write to EKM

1. After **stage 7** is in the completed list, **Write to EKM…** enables.
2. Review the write-back plan in the confirmation dialog.
3. Approve → saves `<project>/kicad_ai/engineering_knowledge.json`.

### 3. Verify in Notebook

Open **Notebook** (Ctrl+5) → sections such as Circuit Overview, Analysis, Open Items.

See [Workflow: New Project to EKM](Workflows/New_Project_to_EKM.md).

---

## EKM sections after write-back

| Section | Source |
|---------|--------|
| `circuit_overview` | Stage 0 |
| `operation_and_principles` | Stages 1–3 |
| `component_rationale` | Stage 4 |
| `operating_conditions` | Stages 5–6 |
| `analysis` | Stage 7 |
| `recommendations` | Stage 7 (when present) |
| `open_items` | Open questions from all stages |

---

## What gets saved

| Path | Content |
|------|---------|
| `<project>/kicad_ai/engineering_knowledge.json` | EKM document |
| Optional library promotion | Circuit family KB (if `learning_auto_promote` enabled) |

---

## Troubleshooting

### Write to EKM disabled

Complete **stage 7** with a successful **Approve & Send**.

### Parse errors in stage response

Re-run stage; check JSON in response panel; see [AERF Validation Rubric](AERF_Validation_Rubric.md).

### Family mismatch

Set **Circuit family** explicitly or update EKM `aerf_family_id` in Notebook.

---

## Related documents

- [How AERF Works](How_AERF_Works.md)
- [06 — Engineering Notebook](06_Engineering_Notebook.md)
- [AERF Validation Rubric](AERF_Validation_Rubric.md)

## Parent

- [User Guides](README.md)