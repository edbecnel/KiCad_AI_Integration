# Netlist Gap Fill

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Specifications](README.md) › Netlist Gap Fill

> **Status:** Draft
> **Owner:** Project maintainers
> **Applies To:** KiCad AI Integration — AI-assisted netlist and simulation model completion
> **Authoritative:** No

## Purpose

Define how KiCad AI Integration helps when exported or parsed project data is incomplete — either because connectivity is missing from the netlist graph, or because symbols lack usable SPICE/`ngspice` simulation models (`.lib` / `.SUBCKT` definitions).

This feature complements — but does not replace — KiCad's ERC, standard netlist export, and vendor-provided models. AI output is **advisory**; engineers must verify results before simulation or design changes.

## Problem Statement

KiCad projects may have incomplete representation in the data sent to AI:

### Connectivity gaps

- Symbols with unconnected or hidden pins not reflected in exported netlists
- Auto-generated net names (`Net-(D1-Pad2)`) that obscure design intent
- Hierarchical sheets where pin-to-net mapping is fragmented across subsheets
- Legacy or imported symbols missing pin electrical types in the netlist export

### Simulation model gaps

- SPICE netlist exports that omit or stub components without simulation models
- Vendor parts with no public SPICE macromodel (optocouplers, gate drivers, regulators, etc.)
- Baseline `.cir` netlists that reference `.include` / `.lib` files that are missing from the project
- KiCad symbols where `Spice_Model` is unset or points to a non-existent subcircuit

When this information is missing, text-only context limits connectivity audits, isolation checks, netlist-vs-visual cross-references, and SPICE-based analysis.

## Scope

### In scope

**Connectivity gap-fill**

- Detect symbols or pins with incomplete netlist connectivity
- Combine structured extraction JSON, partial netlist, and optional schematic image (600 DPI) for inference
- Return structured output describing inferred pin-to-net assignments

**SUBCKT / `.lib` gap-fill**

- Generate draft `ngspice`-friendly `.lib` files containing `.SUBCKT` definitions for parts missing simulation models
- **Resolve datasheet PDFs** via shared artifact library and per-project registry — deduplicated across projects; track which schematics reference each file
- Support manual user requests (built-in chat) and automated generation at user request
- Produce KiCad hookup notes (`Spice_Model`, pin mapping, `.include` guidance) and provenance metadata
- Classify output by validation status, confidence, and strategy tier (A/B/C)

### Out of scope

- Automatically writing inferred connectivity or generated models back into KiCad schematic files without user review
- Replacing ERC or DRC as authoritative connectivity checks
- Guaranteeing physically accurate or vendor-certified simulation models
- Silent auto-patching of netlists without explicit user opt-in and report disclosure

---

## Artifact library (shared) and per-project registry

KiCad AI Integration uses a **two-layer store**: a **shared artifact library** (one copy of each PDF or `.lib` across projects) and a **per-project `kicad_ai/` registry** that records which schematics and components reference each shared file.

This minimizes duplication when the same part (e.g. `F0D3180`) appears in multiple projects, while keeping a clear audit trail of where each artifact is used.

### Why this is feasible

- KiCad projects are directory-based; the assistant resolves the active `.kicad_pro` path and schematic hierarchy from `pcbnew` or `.kicad_sch` parsing.
- KiCad does **not** need to own these folders — they are assistant metadata.
- A user-level or configured shared path (e.g. `~/kicad_ai_library/`) holds canonical files once; projects link by ID.
- Per-project `kicad_ai/project_manifest.json` tracks references for the open project without copying PDFs per schematic.
- Deduplication by content hash (`sha256`) avoids storing the same datasheet twice under different filenames.

### Recommended layout

**Shared library** (config: `artifact_library_path`, default `~/kicad_ai_library/`):

```text
~/kicad_ai_library/
  catalog.json             # global index + cross-project reference tracking
  url_fetch_log.json       # per-part HTTPS URL outcomes (downloaded / failed)
  datasheets/
    F0D3180.pdf            # one canonical file per unique content/part
  libs/
    F0D3180.lib
```

**Per-project registry** (beside `.kicad_pro`):

```text
<project_root>/
  myproject.kicad_pro
  myproject.kicad_sch
  kicad_ai/
    project_manifest.json  # this project's links into the shared catalog
    exports/               # project-local only (schematic PNG cache, run snapshots)
```

The tool **creates** both locations on first use. Shared files are written once; subsequent projects **link** to the existing catalog entry.

### `catalog.json` (shared library)

Global index with **reference tracking across schematics and projects**:

```json
{
  "version": 1,
  "library_path": "/Users/me/kicad_ai_library",
  "artifacts": [
    {
      "id": "ds-F0D3180-a1b2c3",
      "type": "datasheet",
      "part": "F0D3180",
      "file": "datasheets/F0D3180.pdf",
      "sha256": "…",
      "source": "user_attach",
      "referenced_by": [
        {
          "project_path": "/projects/flyback_driver/flyback_driver.kicad_pro",
          "project_name": "flyback_driver",
          "schematics": ["flyback_driver.kicad_sch"],
          "components": [
            { "reference": "U3", "sheet_path": "flyback_driver.kicad_sch", "sheet_name": "/" }
          ]
        },
        {
          "project_path": "/projects/plc_board/plc_board.kicad_pro",
          "project_name": "plc_board",
          "schematics": ["plc_board.kicad_sch", "power.kicad_sch"],
          "components": [
            { "reference": "U1", "sheet_path": "power.kicad_sch", "sheet_name": "power" }
          ]
        }
      ]
    },
    {
      "id": "lib-F0D3180-d4e5f6",
      "type": "lib",
      "part": "F0D3180",
      "file": "libs/F0D3180.lib",
      "tier": "datasheet_backed",
      "generated": "2026-07-14T09:00:00Z",
      "referenced_by": [ "…" ]
    }
  ]
}
```

### `project_manifest.json` (per project)

Lightweight view of **this project's** links into the shared catalog:

```json
{
  "project_path": "/projects/flyback_driver/flyback_driver.kicad_pro",
  "project_name": "flyback_driver",
  "links": [
    {
      "artifact_id": "ds-F0D3180-a1b2c3",
      "part": "F0D3180",
      "components": [{ "reference": "U3", "sheet_path": "flyback_driver.kicad_sch" }]
    }
  ]
}
```

On each gap-fill or context-collection run, the tool **refreshes** `referenced_by` from the active schematic(s) so the catalog reflects current symbol usage. Stale entries (component removed from schematic) may be pruned on scan or marked inactive.

### Deduplication and linking

| Situation | Behavior |
|-----------|----------|
| First attach of `F0D3180.pdf` | Copy into shared `datasheets/`; create catalog entry; add project link |
| Same PDF content (matching `sha256`) already in catalog | **Link only** — no second copy; append `referenced_by` for this project/component |
| Same part number, different PDF hash | New catalog entry (version conflict surfaced in UI) |
| SUBCKT generated for part already in catalog | Write or update `libs/<part>.lib`; link from project manifest |
| User deletes component from schematic | Next scan removes or soft-deletes that component from `referenced_by` |

Shared artifacts are **not deleted** from the library while any project still lists them in `referenced_by`.

### How files get registered

| Action | Result |
|--------|--------|
| User attaches PDF in gap-fill UI | Store in shared library (or link if duplicate); update catalog + project manifest |
| Symbol `Datasheet` URL fetched | Cache PDF in shared library; record provenance; link project |
| SUBCKT generation succeeds | Write `libs/<part>.lib` in shared library; link from project manifest |
| Resolver finds symbol `Datasheet` local path | If outside shared library, offer import-into-library (copy once, then link) |

### Reference from KiCad symbols

Resolver order prefers **catalog lookup by part/value/reference** before raw path parsing. After registration, optionally suggest updating the symbol `Datasheet` field to a stable pointer:

```text
kicad_ai://ds-F0D3180-a1b2c3
```

or a path relative to the shared library if the user prefers plain files:

```text
${KICAD_AI_LIBRARY}/datasheets/F0D3180.pdf
```

(`${KICAD_AI_LIBRARY}` expands from `artifact_library_path` in user config.) Per-project symlinks under `<project>/kicad_ai/datasheets/` → shared file are an optional portability aid for tools that require local paths.

### Hierarchical schematics

Track **sheet path** and **sheet name** in `referenced_by`, not only root schematic:

- Root sheet: `flyback_driver.kicad_sch`
- Subsheet: `power.kicad_sch` instantiated as sheet `power`
- Same shared PDF may be referenced by `U3` on root and `U1` on subsheet — both recorded under the same project entry or split by schematic file as needed

### Configuration

| Setting | Purpose | Default |
|---------|---------|---------|
| `artifact_library_path` | Shared library root | `~/kicad_ai_library/` |
| `datasheet_search_paths` | Additional folders to import from (legacy/global) | `[]` |

### Version control

- **Shared library:** optional dedicated git repo or team sync path for datasheets and generated libs used across projects.
- **Per-project `kicad_ai/`:** commit `project_manifest.json`; gitignore `exports/` if machine-local.
- **Portable teams:** set `artifact_library_path` to a shared network or repo path all engineers use.

### Security and privacy

- Shared library is user-scoped unless configured to a team path.
- Catalog records **which projects and schematics** reference each file — required for safe deduplication and deletion policy.
- URL fetch cache writes to the shared library, not per-project duplicates.
- Cloud AI transmission still requires explicit user approval; catalog entries appear in context preview.

---

## Datasheet acquisition (before SUBCKT generation)

SUBCKT quality depends on **finding datasheets the user already has**, not on sending the user to hunt online. Vendor pages often lack SPICE models and may not yield usable PDFs. The Context Collection Engine must **resolve datasheet artifacts automatically** before choosing a generation strategy.

### Resolution priority

Try sources in this order; stop at the first usable PDF or structured document:

| Priority | Source | Notes |
|----------|--------|-------|
| 1 | **Shared artifact library** | `catalog.json` + `datasheets/` / `libs/` — dedupe by `sha256`; see [Artifact library](#artifact-library-shared-and-per-project-registry) |
| 2 | **Per-project `kicad_ai/project_manifest.json`** | Links active project/components to shared catalog entries |
| 3 | **Symbol `Datasheet` field — local file** | Import into shared library if not already cataloged |
| 4 | **User attach via UI** | Store in shared library (or link); update catalog + project manifest |
| 5 | **User config `datasheet_search_paths`** | Import-once into shared library when matched |
| 6 | **Symbol `Datasheet` field — URL fetch** | `https:` only; cache to shared library; update `referenced_by`; skip URLs already logged in `url_fetch_log.json` |
| 7 | **Other symbol fields + footprint metadata** | Matching hints only |
| 8 | **AI datasheet discovery** *(future)* | When step 6 fails, hand off to AI provider with KiCad symbol context — see [URL fetch log](#url-fetch-log-and-ai-datasheet-discovery) |

**Not a primary workflow:** asking the user to search the web for a datasheet. The UI may offer optional manual URL entry or file attach when resolution fails, but must not block generation on a web search.

### URL fetch log and AI datasheet discovery

The shared library maintains `url_fetch_log.json` so HTTPS datasheet URLs are **not revisited** once an outcome is known. Each entry is keyed by **part number (`Value`) + normalized URL** and records:

| Field | Description |
|-------|-------------|
| `part` | Symbol `Value` at resolution time |
| `source_url` | Normalized `https:` URL from the symbol `Datasheet` field |
| `status` | `downloaded` or `failed` |
| `artifact_id` | Catalog entry when `downloaded` |
| `error` | Last fetch error when `failed` |
| `updated_at` | ISO-8601 UTC timestamp |

**Behavior:**

- **`downloaded`** — skip network fetch; resolve from `artifact_id` / catalog when policy is `if_missing`
- **`failed`** — skip network fetch; set `DatasheetResolution.needs_ai_datasheet_discovery = true` and `url_fetch_outcome = failed`
- **Bot protection (403 / HTML “access denied”)** — Mouser, Littelfuse (Akamai), and similar hosts often allow browser downloads but block scripted clients. Prefer **direct manufacturer PDF URLs** in symbol `Datasheet` fields (e.g. `onsemi.com/.../fod3180-d.pdf` instead of a Mouser redirect). Manual attach remains supported.
- **New URL on same part** — if the user updates the symbol `Datasheet` field, the new URL is tried (log key includes URL)
- **`always` fetch policy** — re-fetch successful URLs; still skip URLs logged as `failed` (see [Force refresh datasheets](#force-refresh-datasheets-future-ui))

When `needs_ai_datasheet_discovery` is set, the Context Collection Engine has exhausted automatic resolution for that symbol's current URL. **Phase 1 stretch slice** records the handoff only; the AI Provider Layer (not yet implemented) should:

1. Collect KiCad context for the part — `Value`, `Footprint`, pin table, custom fields (`MPN`, manufacturer), optional schematic image
2. Ask the model for an **official manufacturer `https:` PDF URL** (not open-ended web search as default UX)
3. Present suggested URL(s) in the context preview for **user approval** before fetch
4. On approval, fetch via the same SSRF-safe `url_fetch` path, register in catalog, and update `url_fetch_log` to `downloaded`
5. If discovery fails, continue with **Tier B** (context synthesis) or **Tier C** (last-resort inference) — never block the user

Implementation tracking: [MASTER_TASK_LIST](../../tasks/MASTER_TASK_LIST.md) — *AI-assisted datasheet discovery when URL fetch fails*.

### Force refresh datasheets (future UI)

Users need an explicit **Force refresh datasheets** action (in-KiCad UI; not required on every run) to re-download PDFs from symbol `Datasheet` HTTPS URLs after correcting links, replacing stale cached files, or recovering from transient fetch failures.

**Expected behavior when the user chooses force refresh:**

1. Scope — all placed symbols on the active project schematics that have an `https:` `Datasheet` URL (optionally: selected components only in a later iteration)
2. Bypass catalog cache — re-fetch even when a PDF is already in `catalog.json` / `project_manifest.json`
3. Bypass `url_fetch_log` — retry URLs previously logged as `failed` or `downloaded` for the current part+URL pair
4. Update shared library — replace or re-register catalog entries; refresh `url_fetch_log` to `downloaded` or `failed` with new timestamps
5. Show progress — per-part status (`downloading`, `downloaded`, `failed`) in the UI; do not block other assistant features on completion

**Partial backend support today (CLI / config only):**

- `datasheet_url_fetch: "always"` or `--fetch-always` re-downloads when a cached PDF exists, but **still skips** URLs logged as `failed` in `url_fetch_log.json`
- Full force refresh requires a dedicated resolver flag (e.g. `force_refresh=True`) that ignores `url_fetch_log` and always attempts HTTPS fetch — **not yet implemented**

**UI placement (planned):** context collection preview or artifact library panel — alongside attach PDF, add search folder, and future AI discovery actions.

Implementation tracking: [MASTER_TASK_LIST](../../tasks/MASTER_TASK_LIST.md) — *Force refresh datasheets (user-facing)*.

### KiCad symbol properties

KiCad symbols commonly carry a standard **`Datasheet`** property (URL or file path) on the library symbol and schematic instances. The Context Collection Engine should extract from `.kicad_sch` (and symbol libraries when resolvable):

- `Reference`, `Value`, `Footprint`
- `Datasheet` — primary artifact pointer
- `Spice_Model`, `Spice_Lib`, `Spice_Primitive` when present
- Custom fields (e.g. `MPN`, `Vds_max`, manufacturer)

Path resolution rules:

- Relative paths → resolve against project root (directory containing `.kicad_pro`)
- `file://` URLs → normalize to local path
- `https:` URLs → fetch only if allowed by policy; cache result for reuse; default **10s** connect/response timeout (`url_fetch_timeout_sec`) plus **60s** PDF read timeout (`url_fetch_read_timeout_sec`) — slow vendor CDNs (e.g. Littelfuse) may need the full connect budget
- KiCad variable substitution (e.g. `${KICAD_USER_TEMPLATE_DIR}`) → expand when possible

### User PDF registration

When automatic resolution fails, support explicit registration without web search. See **[Datasheet Requirements and User PDF Supply](Datasheet_Requirements_and_User_Supply.md)** for when PDFs are required vs optional, user notification rules, and the planned drag-and-drop UI.

**Today (no wxPython UI yet):**

- **Manual drop** — save as `{artifact_library_path}/datasheets/<Value>.pdf` using the schematic **Value** field; re-run context collection (catalog lookup by part).
- **Programmatic attach** — `DatasheetResolver.resolve_symbol(..., user_attach_path=…)` registers in catalog + project manifest (backend ready; UI not wired).
- **Search folder** — `datasheet_search_paths` in config for an inbox directory.

**Planned UI:**

- **Drag-and-drop** — drop PDF onto a part row or drop zone; file copied to shared `datasheets/`, `catalog.json` + `project_manifest.json` updated, optional symbol `Datasheet` field update.
- **Missing required datasheets panel** — list parts with `fetch_failed` / `missing` where a PDF is **required** (active silicon, drivers, specialized diodes); amber highlight before Approve & Send.

**User notification:** CLI prints a **Manual datasheets required** section when auto-fetch failed for datasheet-required parts. UI must show the same list with attach/drop actions.

Legacy bullets:

- **Per-component attach** — user picks a PDF; store in shared library (link if duplicate `sha256`); update catalog `referenced_by` and project manifest
- **Optional: offer to update symbol `Datasheet` field** to catalog URI or `${KICAD_AI_LIBRARY}/…` path after attach (user confirms)

Registered PDFs are reused on subsequent runs for the same project.

---

## SUBCKT generation — strategy tiers

The automated feature and built-in chat **must use the richest evidence available**. Part-number-only prompts are **inadequate** and are not an acceptable default.

| Tier | Name | When | Approach |
|------|------|------|----------|
| **A** | Datasheet-backed | PDF resolved from symbol field, local library, or user registration | Two-stage: extract structured facts from PDF → synthesize `.SUBCKT` → validate |
| **B** | Multi-source context synthesis | No PDF, but KiCad symbol pins, footprint, fields, schematic JSON, optional 600 DPI image, netlist context | Multi-step AI: pin-accurate behavioral/macro model constrained by symbol definition; label `context_synthesized` |
| **C** | Last-resort inference | No PDF and thin project context | AI uses part identity plus any scraps (value string, footprint name, schematic crop); heavy assumptions; label `inferred — needs manual review`; **never** imply datasheet accuracy |

### Tier A workflow (default when PDF is available)

Do **not** go directly from raw PDF text to final `.SUBCKT` in one step.

1. **Extract structured component facts** from the resolved PDF — pinout, electrical characteristics, absolute maximum ratings, operating conditions, behavior notes, unknowns, confidence per fact
2. **Synthesize candidate `.SUBCKT`** from extracted facts at `datasheet_constrained` or `behavioral` abstraction
3. **Validate** — `.SUBCKT`/`.ENDS` consistency, pin count vs KiCad symbol, `ngspice`-friendly syntax; optional smoke test
4. **Emit KiCad notes** — `Spice_Model`, pin-order warnings vs symbol, example `.include` line
5. **Record provenance** — which PDF path or cache entry was used

Note: a datasheet PDF rarely contains SPICE models directly. Tier A uses the datasheet for **pinout and electrical limits**, then **synthesizes** an `ngspice`-friendly macro-model — it does not expect vendor SPICE netlists in the PDF.

### Tier B workflow (no PDF — primary fallback)

When no PDF resolves, combine **all** KiCad and project context before calling the model:

- Symbol pin list with names, numbers, and electrical types (match generated `.SUBCKT` pin order to **KiCad symbol**, not guessed datasheet order)
- Value, footprint, and custom fields from the schematic instance
- Optional schematic image (600 DPI) for reference designator and surrounding circuitry
- Neighboring components and nets from extraction JSON
- Explicit instruction: behavioral/macro model only; list every assumption; flag parameters that could not be verified

Do **not** collapse Tier B to a single-line part-number prompt.

### Tier C workflow (last resort)

Only when Tier A and B inputs are insufficient. The model may use general knowledge about the part family, but output must:

- Use abstraction level `behavioral` or `placeholder`
- Include a prominent `limitations` and `unverified_parameters` section
- Set validation status to `needs-manual-review` at minimum
- Never be labeled as datasheet-backed

Historical one-liner (part number only) — **not recommended**:

```text
Can you create an ngspice-friendly SUBCKT .lib file for this part: F0D3180?
```

This may produce a quick sketch for manual experimentation outside the tool, but the built-in assistant **must not** use this as its automated prompt template.

---

## Manual workflow (do it yourself)

Users may generate `.lib` files outside KiCad AI Integration. Prefer the same evidence ordering as the automated feature.

### If you have the PDF

Attach the datasheet PDF (from your symbol field, project `datasheets/` folder, or disk) and use:

```text
Using the attached datasheet PDF and the KiCad symbol pin list below, create an
ngspice-friendly .lib with one .SUBCKT for <PART_NUMBER>.

Stage 1 — Return structured JSON facts only (pinout, limits, key parameters, unknowns).
Stage 2 — After I confirm facts, generate the .lib matched to this KiCad pin order:

<KICAD_SYMBOL_PINS>

Requirements:
- Behavioral/macro model unless the datasheet supports more
- Match .SUBCKT pin order to the KiCad symbol pin list, not guessed datasheet order
- List assumptions, unknowns, and limitations
- Provide recommended Spice_Model and .include guidance
```

### If you do not have the PDF

Do not rely on a web search alone. Gather from KiCad:

- Symbol pin table (copy from Symbol Editor or extraction output)
- Value, footprint, and all symbol fields
- Optional schematic screenshot

Use the Tier B style prompt above without a PDF attachment. Treat the result as **draft** until verified against a real datasheet or bench measurement.

### After receiving AI output — manual checklist

1. Cross-check pin names and order against your KiCad symbol
2. Run `ngspice` parse or smoke test on the `.lib` if available
3. Set the symbol `Spice_Model` field per the KiCad notes
4. Add `.include path/to/part.lib` to your exported SPICE netlist if needed
5. Do not treat the model as production-ready without datasheet or measurement verification

See [Verification](../AI/Verification.md).

---

## Built-in chat and automated feature

### Triggers

1. **User-initiated (primary)** — "Generate SUBCKT model for selected component" or natural-language request in the in-KiCad chat
2. **Simulation gap-detect (optional, later)** — SPICE export or BOM flags parts missing `Spice_Model` or unresolved `.lib` references
3. **Connectivity auto-detect (optional, later)** — incomplete pin connectivity in netlist graph

Automated SUBCKT generation is **opt-in** and **never silent**. Context preview shows resolved datasheet path (or "no PDF — using context synthesis") before Approve & Send.

### Automated routing logic

When the user requests SUBCKT / `.lib` generation:

1. **Resolve datasheet** — symbol `Datasheet` field → local paths → user search paths → registered attachments → controlled URL fetch (respecting `url_fetch_log.json`) → **AI discovery when logged `failed`** *(future)* → cache
2. If PDF resolved → **Tier A** (two-stage extract + synthesize + validate)
3. Else if symbol pins + value/footprint/fields (and optionally schematic image) → **Tier B** (multi-source context synthesis)
4. Else → **Tier C** (last-resort inference with mandatory review labeling)
5. Always emit validation status, provenance (`datasheet_path` or `sources_used[]`), and KiCad hookup notes

The UI must **not** require the user to find a datasheet online before proceeding. If resolution fails, offer **attach PDF** and **add search folder** actions, then continue with Tier B or C.

### Expected SUBCKT output (automated / built-in chat)

Deliverables per component:

| Artifact | Description |
|----------|-------------|
| `generated.lib` | `ngspice`-friendly `.SUBCKT` text |
| `kicad-notes.md` | `Spice_Model`, pin mapping, `.include` example, warnings |
| `validation.json` | `syntax-valid`, `syntax-valid-with-warnings`, `needs-manual-review`, or `failed-validation` |
| `assumptions.md` | Simplifications, unknowns, abstraction level |
| `provenance.json` | Resolved PDF path, symbol field values, or `sources_used` for Tier B/C |
| `tier` | `datasheet_backed`, `context_synthesized`, or `inferred_last_resort` |

### Connectivity gap-fill output

When inferring missing pin-to-net assignments, use structured JSON in `<kicad_netlist_gap_fill>`:

```json
{
  "inferences": [
    {
      "reference": "U1",
      "pin": "15",
      "inferred_net": "PICO_GPIO15",
      "confidence": "high",
      "evidence": "Visual wire to local label PICO_GPIO15 on sheet root"
    }
  ],
  "ambiguous": [
    {
      "reference": "Q2",
      "pin": "2",
      "note": "Multiple candidate nets; requires engineer confirmation"
    }
  ],
  "unresolved": [
    {
      "reference": "J1",
      "pin": "3",
      "note": "Pin not visible in provided schematic image crop"
    }
  ]
}
```

---

## Inputs

| Input | Connectivity gap-fill | SUBCKT Tier A | SUBCKT Tier B | SUBCKT Tier C |
|-------|----------------------|---------------|---------------|---------------|
| Partial netlist / connectivity graph | Yes | Recommended | Yes | Optional |
| Schematic extraction JSON | Yes | Yes | Yes | Optional |
| Schematic image (600 DPI) | Recommended | Recommended | Recommended | Optional |
| Part number / value | — | Yes | Yes | Yes |
| Resolved datasheet PDF | — | Yes | — | — |
| Symbol `Datasheet` field (path/URL) | — | Yes (resolution) | Yes (if fetch fails) | Optional |
| User-registered / cached PDF | — | Yes | — | — |
| Local `datasheet_search_paths` | — | Yes (resolution) | — | — |
| KiCad symbol pin list | — | Yes | Yes | If available |
| Footprint + custom fields | — | Recommended | Yes | Optional |
| ERC results | Recommended | Optional | Optional | Optional |
| User design intent | Optional | Optional | Optional | Optional |

Schematic image export: [ADR-0004](../Architecture/ADRs/ADR-0004-Optional-Multimodal-Schematic-Context.md).

---

## Verification requirements

Before using gap-fill output:

**Connectivity**

1. Cross-check each inferred connection against the schematic in KiCad
2. Run or review ERC for affected nets and pins
3. Reject or correct any inference marked `ambiguous` or `unresolved`

**SUBCKT / `.lib` models**

1. Verify pin order against the KiCad symbol — generated `.SUBCKT` pins must match the symbol, not an assumed datasheet order
2. Review provenance: confirm which PDF or context sources were used
3. Review assumptions and unknowns; reject models with unresolved pinout
4. Run `ngspice` parse or smoke test when available
5. Treat Tier B (`context_synthesized`) and Tier C (`inferred_last_resort`) as drafts requiring datasheet or bench verification
6. Do not commit generated `.lib` files without engineering review

See [Verification](../AI/Verification.md).

---

## Limitations

- AI may hallucinate connections or electrical parameters
- Datasheet PDFs describe physical parts, not SPICE models — synthesis is always an approximation
- Web datasheet URLs in symbol fields may be stale, blocked, or PDFs without simulation-relevant tables
- Hidden pins, bus entries, and off-sheet connectors are high-risk inference targets
- Gap-fill quality depends on symbol field completeness (`Datasheet`, pin definitions, custom ratings)
- Tier C last-resort output must not be used for production simulation without review
- Generated models are not vendor-certified SPICE models

---

## Decisions

| Question | Decision |
|----------|----------|
| What scenarios does gap-fill target? | Missing connectivity in netlists **and** missing SPICE `.lib`/`.SUBCKT` models for symbols |
| How are datasheets obtained? | **Shared artifact library** + per-project manifest; symbol fields; attach UI; controlled URL fetch |
| Artifact storage model? | **Shared library** (`artifact_library_path`) for files; **per-project `kicad_ai/`** for links and `referenced_by` tracking across schematics |
| Cross-project deduplication? | **Yes** — same `sha256` links without copying; catalog tracks all projects/schematics/components per artifact |
| URL in symbol field? | Fetch only if `https:` and policy allows; cache PDF locally; never require user to hunt online |
| No PDF available? | **Tier B** multi-source KiCad context synthesis, then **Tier C** last-resort inference with review labeling |
| Part-number-only prompt? | **Rejected** for built-in automation; documented only as discouraged manual shortcut |
| Output format? | `.lib` + `kicad-notes.md` + `validation.json` + `provenance.json` for SUBCKT; JSON for connectivity |
| Write back to KiCad? | **No** — advisory output only; user applies changes manually |

---

## Related Documents

- [Prompt Architecture](../Architecture/Prompt_Architecture.md) — gap-fill and SUBCKT prompt templates
- [ADR-0004: Optional Multimodal Schematic Context](../Architecture/ADRs/ADR-0004-Optional-Multimodal-Schematic-Context.md)
- [AI Tools for Advanced Circuit Analysis](../Reference/AI_Tools_for_Advanced_Circuit_Analysis.md)
- [Master Task List](../../tasks/MASTER_TASK_LIST.md) § 1.1, § 1.3
- [Verification](../AI/Verification.md)

## Parent

- [Specifications](README.md)
