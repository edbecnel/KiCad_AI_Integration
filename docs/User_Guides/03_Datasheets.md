# Datasheets
[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [User Guides](README.md) › Datasheets


[Home](../../README.md) · [User Guides](README.md) · Datasheets

## Overview

The **Datasheets** tab manages PDF datasheets for parts that need them for SUBCKT generation and detailed AI analysis. PDFs live in a **shared library** (`~/kicad_ai_library/` by default) and are linked to schematic symbol **Value** fields.

**Rationale:** AI analysis of custom parts (transformers, complex ICs) requires datasheet text. This tab is separate from Chat — attach and resolve PDFs here first.

## Who this is for

Anyone with custom or non-passive parts that lack resolved datasheet PDFs.

## Before you begin

- **Refresh context** in the Assistant shell
- PDFs on disk or HTTPS URLs in symbol fields (optional)

## How to open it

- **Ctrl+2** or **Datasheets** tab
- CLI: `--ui-datasheets`

---

## UI reference

### Top

| Control | Purpose |
|---------|---------|
| **Use AI to find datasheets** | Opt-in Anthropic URL discovery (may incur cost) |

### Sub-tabs

| Tab | Shows |
|-----|--------|
| **Missing** | Parts needing PDFs |
| **All required** | All parts that require datasheets (+ PDF column) |
| **Symbol field** | Parts with empty, local, or failed symbol Datasheet property |

**Symbol field** tab also has: **After reset/attach/write: update symbol Datasheet with resolved HTTPS URL**

### Per-row actions

Select a row first.

| Button | Purpose |
|--------|---------|
| **Attach PDF…** | File picker; copies into artifact library |
| **Reset & re-resolve…** | Clear cached link; optional delete orphan PDF; optional re-run AI |
| **Find with AI** | Discover HTTPS URLs (needs API key + checkbox enabled) |
| **Open URL** | Open suggested URL in browser |
| **Copy manual path** | Copy expected library path for manual drop |
| **Write URL to schematic** | Write resolved HTTPS URL to symbol Datasheet field |
| **Refresh** | Reload list from current context |
| **Force refresh all URLs** | Re-fetch all HTTPS links |
| **Cancel** | Abort long-running worker |

### Status area

**Status** box and progress gauge during reset, fetch, or AI discovery.

**Drag-and-drop:** Drop PDF files onto list controls to attach.

---

## Step-by-step workflow

### Attach a PDF manually

1. **Refresh context**.
2. Open **Datasheets** → **Missing** tab.
3. Select the part row (by Value).
4. Click **Attach PDF…** or drag a PDF onto the list.
5. **Refresh** — row should leave Missing tab; shell badge count decreases.

### AI discovery

1. Enable **Use AI to find datasheets**.
2. Select a missing part → **Find with AI**.
3. Approve URL in dialog if prompted.
4. **Open URL** or let auto-fetch download PDF (per config).

### Reset stale link

1. Select part → **Reset & re-resolve…**
2. Choose options (delete orphan PDF, re-run AI).
3. Re-attach or re-discover.

---

## What gets saved

| Location | Content |
|----------|---------|
| `~/kicad_ai_library/` (configurable) | Shared PDF artifacts by part Value |
| Schematic `.kicad_sch` | Optional Datasheet URL field updates |
| Project context cache | Resolution status on refresh |

---

## Troubleshooting

### Tab badge still shows (N)

Some required parts still lack PDFs — check **Missing** tab.

### Find with AI disabled

Enable checkbox; set API key; select a row on Missing tab.

### HTTPS fetch failed

Use **Attach PDF…** manually or **Reset & re-resolve…**.

---

## Related documents

- [Specifications — Datasheet Requirements](../Specifications/Datasheet_Requirements_and_User_Supply.md)
- [Specifications — AI Datasheet Discovery](../Specifications/AI_Datasheet_Discovery.md)
- [04 — Simulation](04_Simulation_and_SUBCKT.md)

## Parent

- [User Guides](README.md)