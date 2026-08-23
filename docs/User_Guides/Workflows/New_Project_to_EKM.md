# Workflow: New Project to EKM
[Home](../../../README.md) › [Project Index](../../../PROJECT_INDEX.md) › [User Guides](../README.md) › [Workflows](../Step_By_Step_Guides.md) › Workflow: New Project to EKM



## Overview

End-to-end path from a fresh KiCad project to curated **Engineering Knowledge** in the Notebook: datasheets → AERF stages → EKM write-back → verify.

## Prerequisites

- [Getting Started](../00_Getting_Started.md) complete
- Saved `.kicad_pro` / `.kicad_sch`
- API key configured

---

## Steps

### 1. Open Assistant and refresh

1. KiCad PCB Editor → **Tools → External Plugins → KiCad AI Assistant**
2. Confirm project path → **Refresh context**

### 2. Resolve datasheets (Ctrl+2)

1. Open **Datasheets** tab.
2. For each row on **Missing**: **Attach PDF…** or **Find with AI**.
3. **Refresh context** when badge clears.

See [03 — Datasheets](../03_Datasheets.md).

### 3. Run AERF stages (Ctrl+4)

1. Open **AERF** tab.
2. Set **Circuit family** (e.g. `blocking_oscillator`).
3. For stages **0–7**: **Preview stage prompt** → **Approve & Send stage**.
4. When stage 7 completes → **Write to EKM…** → approve.

See [05 — AERF](../05_AERF_Staged_Analysis.md).

### 4. Verify Notebook (Ctrl+5)

1. Open **Notebook** tab.
2. Expand **Circuit Overview**, **Analysis**, **Open Items**.
3. Edit open question **Status** if needed → **Save**.

See [06 — Engineering Notebook](../06_Engineering_Notebook.md).

### 5. Validate on disk

```bash
python scripts/ekm_tool.py validate "$(dirname /path/to/project.kicad_pro)"
python scripts/ekm_tool.py show "$(dirname /path/to/project.kicad_pro)"
```

---

## Expected outcome

- `kicad_ai/engineering_knowledge.json` exists with AERF sections
- Notebook shows readable fields and open questions
- `ekm_tool validate` passes

## Related

- [AERF Validation Rubric](../AERF_Validation_Rubric.md)
- [How AERF Works](../How_AERF_Works.md)

## Parent

- [User Guides](../README.md)
