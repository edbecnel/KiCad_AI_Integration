# Datasheet Requirements and User PDF Supply

[Home](../../README.md) · [Project Index](../../PROJECT_INDEX.md)

> **Documentation path:** [Project Index](../../PROJECT_INDEX.md) → [Specifications](README.md) → Datasheet Requirements and User PDF Supply  
> **Related:** [Netlist Gap Fill](Netlist_Gap_Fill.md) · [MASTER_TASK_LIST](../../tasks/MASTER_TASK_LIST.md)

## Purpose

Define **when** schematic symbols need a datasheet PDF, **how** the assistant notifies the user when automatic download failed, and **how** the user supplies PDFs manually (today and planned UI).

---

## When a PDF is required

Analysis mode matters. The same symbol may be fine for **structural netlist review** but still need a PDF for **SUBCKT / ngspice model generation**.

| Mode | Passives (R, C, L) | Standard diodes / LEDs | Active silicon (ICs, FETs, SCRs, drivers) |
|------|--------------------|-------------------------|-------------------------------------------|
| **Netlist / topology analysis** | Usually **not required** | Often **optional** (training-data defaults) | **Required** for pin-accurate behavior |
| **SUBCKT generation (Tier A)** | N/A (use built-in `.model`) | Often **required** for non-generic parts | **Required** |

The Context Collection Engine classifies each symbol with `datasheet_requirement` (`required`, `optional`, `not_applicable`) for user messaging. Resolution status (`resolved`, `fetch_failed`, `missing`) is independent.

### 1. Fully characterized — no datasheet for netlist analysis

Behavior is standardized and fully described by the schematic **Value** (and reference prefix). The AI can model these from labels alone:

- **Resistors** — e.g. `10k`, `4.7R`; voltage drops and RC time constants from value.
- **Non-polarized capacitors** — ceramic/film values (e.g. `100nF`, `10uF`); generic coupling/decoupling.
- **Standard inductors** — inductance only (e.g. `4.7uH`, `10mH`).
- **Fuses and ferrite beads** — low-resistance shorts for DC/low-frequency analysis.
- **Test points and jumpers** — structural; no active physics.
- **Power symbols** (`#PWR…`, `GND`, rail labels) — net names, not components.

SUBCKT generation for these typically uses ngspice built-in or generic `.model` entries — **no PDF**.

### 2. Contextually defined — soft / conditional

The AI can often infer function from context; a PDF is optional unless you need precise parameters (thermal, efficiency, high-frequency, or SUBCKT):

- **Polarized capacitors** — bulk/decoupling role from net context.
- **Standard signal diodes** (e.g. `1N4148`) — generic ≈0.7 V drop from training data.
- **Standard Zener diodes** — breakdown from value text (e.g. `BZX84C12`).
- **Generic LEDs** — status indicators with ≈2 V drop unless specialized.

### 3. Datasheet required — user must supply if auto-fetch fails

Inform the user explicitly when automatic resolution fails for:

- **Integrated circuits** — MCUs, op amps, gate drivers, optocouplers, DC-DC converters, current sensors, etc.
- **Transistors and FETs** — pinout (G/D/S, B/C/E) is footprint-specific; value alone is insufficient.
- **Specialized power semiconductors** — SiC Schottky, SCRs/thyristors, TVS (e.g. SMBJ series), advanced rectifiers.
- **Any part** targeted for **Tier A SUBCKT** generation.

When HTTPS fetch fails (403 bot protection, bad URL, etc.), the resolver sets:

- `status`: `fetch_failed`
- `needs_ai_datasheet_discovery`: `true` (future AI URL suggestion)
- `url_fetch_outcome`: `failed`

The UI/CLI **must** surface these parts with clear **“PDF required — please supply”** messaging, not silently continue as if analysis were complete.

---

## User notification (required behavior)

After context collection, if any **datasheet-required** symbol has `fetch_failed` or `missing` with an HTTPS URL that could not be retrieved:

1. **List unique part numbers** (Value) affected, with reference count and failure reason.
2. **State that PDFs are required** for SUBCKT / detailed analysis of those parts.
3. **Point to supply methods** below (manual file, UI attach, AI discovery when enabled).
4. **Do not block** netlist-only or Tier B analysis for the rest of the design — but label output as incomplete for the listed parts.

**CLI today:** `scripts/run_ai_assistant.py` prints a **Manual datasheets required** section after the summary when applicable.

**Planned wxPython UI:** context preview panel with an amber/red **“Missing required datasheets”** list before Approve & Send; per-row **Attach PDF** action and links to failed URLs. See [AI Datasheet Discovery Mode](AI_Datasheet_Discovery.md) for optional AI web search and auto-download when direct fetch fails.

---

## AI datasheet discovery mode (planned)

When enabled, the assistant uses an AI provider (with web search) to find official manufacturer PDF URLs for parts where automatic fetch failed, then attempts download via the same SSRF-safe fetch path.

**On failure**, the system records the reason in `url_fetch_log.json` (and a planned `ai_discovery_log.json`), displays the **symbol URL** and any **AI-suggested URL**, and instructs the user to either:

1. **Attach PDF in the UI** — Missing datasheets panel → **Attach PDF…** on the row for that **Value** (maps to all references sharing the Value), or  
2. **Rename manually** — save the browser-downloaded file as `{artifact_library_path}/datasheets/<Value>.pdf` (e.g. `FOD3180.pdf`).

Full specification: [AI Datasheet Discovery Mode](AI_Datasheet_Discovery.md).

---

## How the user supplies PDFs

### Shared library layout

Configured path: `artifact_library_path` (default `~/kicad_ai_library/`).

```text
~/kicad_ai_library/
  catalog.json
  url_fetch_log.json
  datasheets/
    FOD3180.pdf          # canonical filename: part Value + .pdf
    SMBJ18A.pdf
  libs/
```

Per-project links: `<project>/kicad_ai/project_manifest.json`.

### Method 1 — Manual file drop (supported today, no UI)

1. Download the PDF in your browser (required for Littelfuse/Mouser when bot protection blocks auto-fetch).
2. Save as `~/kicad_ai_library/datasheets/<Value>.pdf` using the schematic **Value** field (e.g. `FOD3180.pdf`, `SMBJ18A.pdf`).
3. Re-run context collection. The resolver matches by part in step 1 of the [priority chain](Netlist_Gap_Fill.md#resolution-priority) (`catalog` lookup by part).

**Note:** Files dropped without going through registration still work on the next run if named `{Value}.pdf` and the catalog already has an entry, or after **Method 2** registers them. A future **catalog scan on startup** will pick up new files in `datasheets/` automatically ([MASTER_TASK_LIST](../../tasks/MASTER_TASK_LIST.md)).

### Method 2 — Programmatic attach (API today, UI planned)

`DatasheetResolver.resolve_symbol(..., user_attach_path=Path("..."))` calls `ArtifactStore.register_datasheet`:

- Copies PDF into shared `datasheets/` (dedupe by `sha256`)
- Creates/updates `catalog.json` entry with `part`, `source: user_attach`
- Links component in `project_manifest.json` and `referenced_by`

This is the backend for **per-component attach**; the wxPython UI is not wired yet.

### Method 3 — Drag-and-drop UI (planned)

**Goal:** User drops one or more PDFs onto the assistant panel; each file is registered and mapped to a schematic part.

| Step | Behavior |
|------|----------|
| 1 | User opens **Missing datasheets** or **Artifact library** panel after context collection |
| 2 | User drags PDF onto a row (part `Value`) or onto a drop zone |
| 3 | App validates file is PDF, computes `sha256`, writes to `datasheets/{Value}.pdf` (or retains original name if unique) |
| 4 | Updates `catalog.json` + `project_manifest.json`; sets `url_fetch_log` to `downloaded` if URL was previously `failed` |
| 5 | Optional: prompt to update symbol **Datasheet** field to library path or `kicad_ai://ds-…` URI |
| 6 | Refresh resolution list — part moves to **resolved** / Tier A eligible |

**Drop targeting:**

- **Drop on part row** — bind PDF to that symbol’s `Value` (all references sharing the same Value share one catalog entry).
- **Drop on generic zone** — infer part from filename if it matches `Value` (e.g. `FOD3180.pdf`); otherwise ask user to pick Value from a dropdown of unresolved required parts.

**Implementation tracking:** [MASTER_TASK_LIST](../../tasks/MASTER_TASK_LIST.md) — *Datasheet drag-and-drop UI*.

### Method 4 — Search folder (config)

`datasheet_search_paths` in `~/kicad_ai_config.json` — folders scanned for `{Value}.pdf` during resolution (import-once into shared library). Useful for a local “datasheet inbox” directory.

---

## Recommended symbol `Datasheet` fields

Prefer **direct manufacturer PDF URLs** over distributor links:

| Avoid | Prefer |
|-------|--------|
| `mouser.com/datasheet/...` | `onsemi.com/download/data-sheet/pdf/...` |
| Littelfuse `assetdocs/...` (often 403 for scripts) | Browser download → **Method 1** or manufacturer direct `.pdf` when available |
| Product HTML pages | URL ending in `.pdf` |

---

## Resolution vs requirement matrix

| `datasheet_requirement` | `status` | User action |
|-------------------------|----------|-------------|
| `not_applicable` | `missing` | None |
| `optional` | `missing` / `fetch_failed` | Optional; supply PDF for higher fidelity |
| `required` | `resolved` | None |
| `required` | `fetch_failed` | **Supply PDF** (Methods 1–3), enable [AI discovery](AI_Datasheet_Discovery.md), or fix symbol URL |
| `required` | `missing` (no URL) | **Supply PDF** or set symbol `Datasheet` URL |

---

## Navigation

- [Netlist Gap Fill](Netlist_Gap_Fill.md)
- [AI Datasheet Discovery Mode](AI_Datasheet_Discovery.md)
- [Prompt Architecture](../Architecture/Prompt_Architecture.md)
- [MASTER_TASK_LIST](../../tasks/MASTER_TASK_LIST.md)
