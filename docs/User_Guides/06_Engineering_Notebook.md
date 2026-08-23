# Engineering Notebook

[Home](../../README.md) · [User Guides](README.md) · Engineering Notebook

## Overview

The **Engineering Notebook** is the human-facing editor for the **Engineering Knowledge Model (EKM)** — curated project knowledge: design rationale, AERF conclusions, open questions, and measurements. You edit fields in a structured UI, not raw JSON (though an **Advanced JSON** tab is available).

**Rationale:** EKM is the durable record of what you and the team **approve**. Chat and AERF stages are transient until you write back to EKM.

## Who this is for

Anyone reviewing or editing project engineering knowledge after AERF write-back or manual authoring.

## Before you begin

- **Refresh context** (loads EKM for current project)
- Optional: complete AERF **Write to EKM…** first

## How to open it

- **Ctrl+5** or **Notebook** tab in Assistant shell
- Standalone frame: `--ui-notebook` or `--ui-notebook-panel`

---

## UI reference

| Control | Purpose |
|---------|---------|
| Summary line | Section count, field counts, last updated, dirty flag |
| **Search** / **Clear** | Filter sections and fields |
| **Sections** tab | Collapsible section editors |
| **Advanced JSON** tab | Read-only full EKM document |
| Section header **▶/▼** | Expand/collapse section |
| Field editors | By type: text, enum, number, measurement, reference |
| **Reload** | Discard unsaved edits and reload from disk (confirms if dirty) |
| **Save** | Persist changes to `engineering_knowledge.json` |
| Status line | Save/reload feedback |

### Section types (after AERF write-back)

| Section | Typical content |
|---------|-----------------|
| **Circuit Overview** | Stage 0 determinations, family id |
| **Operation and Principles** | Stages 1–3 JSON |
| **Component Rationale** | Stage 4 |
| **Operating Conditions** | Stages 5–6 |
| **Analysis** | Stage 7 conclusions |
| **Recommendations** | Stage 7 recommendations |
| **Open Items** | Open questions per AERF stage |

### Open Items fields

Each open question shows:

- **Question text** as the field label (full sentence from AERF)
- **Status** dropdown: Pending Review, Resolved, Deferred

Edit status to track review progress; click **Save** to persist.

### Field editor types

| Type | Editor |
|------|--------|
| **text** | Multiline text |
| **enum** | Dropdown (e.g. open question status) |
| **number** | Value + unit |
| **measurement** | Value, unit, conditions |
| **reference** | KiCad link kind, ref, sheet path |

---

## Step-by-step workflow

### 1. View AERF results

1. **Refresh context** after **Write to EKM…**
2. Open **Notebook** (Ctrl+5).
3. Expand sections (e.g. **Analysis**, **Open Items**).

### 2. Edit and save

1. Change field values as needed.
2. Summary shows **(unsaved changes)** when dirty.
3. Click **Save**.

**Expected result:** Status shows saved path; `updated_at` in summary refreshes.

### 3. Search

Type in **Search** to filter sections/fields. **Clear** resets filter.

### 4. Reload from disk

**Reload** → confirm if dirty → re-reads file (discards local edits).

---

## What gets saved

| Path | Content |
|------|---------|
| `<project>/kicad_ai/engineering_knowledge.json` | Full EKM document |

Validate from Terminal:

```bash
python scripts/ekm_tool.py validate "$(dirname /path/to/project.kicad_pro)"
```

---

## Troubleshooting

### Empty notebook

Run AERF **Write to EKM…** or create EKM manually with `ekm_tool init`.

### Cannot close Assistant

Unsaved Notebook edits block close — **Save** or **Reload** and discard.

### Duplicate-looking open questions

Each row is a distinct question from AERF; labels show full question text. Re-run **Write to EKM…** to replace stale open_items fields.

---

## Limitations

- No AI edit proposals from Notebook UI yet — manual field edit only.
- Advanced JSON tab is read-only in the UI.

---

## Related documents

- [05 — AERF](05_AERF_Staged_Analysis.md)
- [ADP-003 Engineering Notebook UI](../Architecture/ADP-003-Engineering-Notebook-User-Interface.md)
- [Workflow: New Project to EKM](Workflows/New_Project_to_EKM.md)

## Parent

- [User Guides](README.md)
