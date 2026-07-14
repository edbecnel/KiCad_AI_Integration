# AI Datasheet Discovery Mode

[Home](../../README.md) · [Project Index](../../PROJECT_INDEX.md)

> **Documentation path:** [Project Index](../../PROJECT_INDEX.md) → [Specifications](README.md) → AI Datasheet Discovery  
> **Related:** [Datasheet Requirements and User PDF Supply](Datasheet_Requirements_and_User_Supply.md) · [Netlist Gap Fill](Netlist_Gap_Fill.md) · [MASTER_TASK_LIST](../../tasks/MASTER_TASK_LIST.md)  
> **Status:** Specified — not yet implemented

## Purpose

Define an optional **AI datasheet discovery mode** that searches for official manufacturer PDF URLs when automatic HTTPS fetch from the symbol `Datasheet` field fails, downloads them when possible, and records failures with actionable guidance for manual supply via the UI or file rename.

---

## When it runs

AI discovery is **opt-in** (config, CLI flag, or UI toggle). It does not run on every context collection by default.

| Trigger | Condition |
|---------|-----------|
| User enables **AI datasheet discovery mode** | Explicit setting (`datasheet_ai_discovery: true` in config, `--ai-datasheets` CLI, or UI checkbox) |
| Per-part eligibility | `DatasheetResolution.needs_ai_datasheet_discovery == true` **or** datasheet-required part with `status` in (`fetch_failed`, `missing`) and no resolved PDF |
| Skip | Part already `resolved` from catalog, manifest, local file, or prior successful fetch |

**Resolution order with AI mode enabled** (extends [Netlist Gap Fill priority chain](Netlist_Gap_Fill.md#resolution-priority)):

1. Steps 1–7 unchanged (catalog → manifest → local paths → search paths → URL fetch).
2. **Step 8 — AI datasheet discovery** (this spec): search → suggest URL → auto-fetch → register or record failure.
3. If step 8 fails, surface **manual supply** instructions (UI attach or `{Value}.pdf` rename).

---

## AI discovery workflow

```text
For each eligible part (unique Value):
  1. Build symbol context (Value, Footprint, lib_id, pin names, custom fields, failed URL + error)
  2. AI web search / URL suggestion — prefer official manufacturer PDF ending in .pdf
  3. Validate suggested URL (https only, SSRF-safe allowlist rules — same as url_fetch)
  4. Attempt download via existing url_fetch path
  5a. Success → register in catalog, update url_fetch_log (downloaded), link manifest
  5b. Failure → record in url_fetch_log + ai_discovery_log with reason; show user manual path
```

### Symbol context sent to the model

Minimum fields per part:

- `Value` (part number)
- `Reference` (example ref), reference count for that Value
- `Footprint`, `lib_id`
- Pin table from schematic symbol (number + name)
- Custom properties when present (`MPN`, manufacturer, etc.)
- Current symbol `Datasheet` URL (if any) and **last fetch error** from `url_fetch_log.json`

Optional: schematic image crop around the component (future).

### URL selection rules

The model (or search tool) should prioritize, in order:

1. Direct manufacturer PDF (`*.pdf` on manufacturer domain)
2. Authorized distributor direct PDF (only if manufacturer link unavailable)
3. Never auto-fetch HTML product pages, login walls, or non-HTTPS links

**User approval (recommended for Phase 1):** Present top suggested URL(s) in UI before fetch. **Auto-fetch without approval** may be allowed when the user explicitly enables “AI auto-download” in settings.

### Download and registration

Successful download uses the same pipeline as step 6 URL fetch:

- SSRF-safe [`url_fetch`](../../src/utils/url_fetch.py)
- Register via `ArtifactStore.register_datasheet` with `source: ai_discovery`
- Update `url_fetch_log.json`: `status: downloaded`, `artifact_id`, `source_url` = discovered URL
- Optional: offer to update symbol `Datasheet` field to the working URL

---

## Failure recording

When AI discovery cannot produce a usable PDF, persist a durable record so the user is not prompted to retry blindly.

### `url_fetch_log.json` (existing)

Continue to key by **part + normalized URL**. For AI-discovered URLs that fail fetch:

| Field | Value |
|-------|--------|
| `status` | `failed` |
| `error` | Human-readable reason (bot protection, 404, not a PDF, timeout, etc.) |
| `source_url` | The URL that was attempted (symbol field URL or AI-suggested URL) |

### `ai_discovery_log.json` (planned, shared library)

One entry per **part + discovery attempt** when AI mode runs:

| Field | Description |
|-------|-------------|
| `part` | Symbol `Value` |
| `attempted_at` | ISO-8601 UTC |
| `symbol_datasheet_url` | Original symbol field URL, if any |
| `suggested_urls` | Ordered list of URLs the AI considered |
| `selected_url` | URL chosen for fetch attempt |
| `outcome` | `downloaded`, `fetch_failed`, `no_url_found`, `user_rejected` |
| `error` | Failure message when `outcome` is not `downloaded` |
| `artifact_id` | Set when downloaded |

### User-facing failure message (required)

For each failed part, UI and CLI **must** show:

1. **Part Value** and reference count
2. **Why it failed** — copy of `error` (e.g. “Site blocked automated download (bot protection)”)
3. **URL(s) to try manually** — symbol field URL and/or AI-suggested URL, as clickable links where the host supports browser download
4. **Manual import instructions** — two equivalent paths:

   **Path A — UI attach (preferred)**  
   Open **Missing required datasheets** → select the row for `{Value}` → **Attach PDF…** → file is registered and mapped to all symbols with that Value.

   **Path B — File rename**  
   Download the PDF in your browser, save as:

   ```text
   {artifact_library_path}/datasheets/{Value}.pdf
   ```

   Example: `~/kicad_ai_library/datasheets/FOD3180.pdf` for Value `FOD3180`. Re-run context collection.

5. **Do not block** the rest of the design for netlist-only / Tier B work — mark analysis incomplete for listed parts only.

Example CLI-style block (UI should mirror):

```text
FOD3180 (7 refs): AI discovery failed — Site blocked automated download (bot protection)
  Symbol URL: https://www.mouser.com/datasheet/2/149/FOD3180-1008860.pdf
  Suggested URL: https://www.onsemi.com/download/data-sheet/pdf/fod3180-d.pdf
  Manual: Attach PDF in Missing datasheets panel, or save as ~/kicad_ai_library/datasheets/FOD3180.pdf
```

---

## Configuration (planned)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `datasheet_ai_discovery` | bool | `false` | Enable step 8 after URL fetch failure |
| `datasheet_ai_discovery_auto_fetch` | bool | `false` | Fetch suggested URL without per-URL approval |
| `datasheet_ai_discovery_max_urls` | int | `3` | Max suggested URLs to try per part per run |

CLI (planned): `--ai-datasheets`, `--ai-datasheets-auto-fetch`

---

## UI integration

| Surface | Behavior |
|---------|----------|
| Context collection / Missing datasheets panel | Toggle **Use AI to find datasheets**; run discovery for unresolved required parts |
| Per-row status | `Searching…`, `Downloading…`, `Resolved`, `Failed — attach manually` |
| Failed row actions | **Attach PDF…**, **Open URL in browser**, copy manual path `{library}/datasheets/{Value}.pdf` |
| After attach | Re-resolve; clear row when `status == resolved` |

See [Datasheet Requirements — Method 2 & 3](Datasheet_Requirements_and_User_Supply.md#how-the-user-supplies-pdfs) for attach and drop-zone behavior.

---

## Security and cost

- Reuse SSRF rules from `url_fetch` — no `file://`, no private IP ranges, HTTPS only
- Log all AI-suggested URLs for audit
- Rate-limit discovery per project run; dedupe by part Value
- AI discovery is a **paid API / search tool** operation — show estimated cost or require explicit user opt-in

---

## Implementation tracking

| Item | Status |
|------|--------|
| `needs_ai_datasheet_discovery` flag on resolution | Done (stretch slice) |
| `url_fetch_log.json` failed URL skip | Done |
| AI provider + search tool integration | Not started |
| `ai_discovery_log.json` | Not started |
| Config / CLI flags | Not started |
| UI toggle + progress in Missing datasheets panel | Not started |
| Enhanced failure messages with suggested URL | Not started |

See [MASTER_TASK_LIST](../../tasks/MASTER_TASK_LIST.md) — *AI-assisted datasheet discovery when URL fetch fails*.

---

## Navigation

- [Datasheet Requirements and User PDF Supply](Datasheet_Requirements_and_User_Supply.md)
- [Netlist Gap Fill](Netlist_Gap_Fill.md)
- [MASTER_TASK_LIST](../../tasks/MASTER_TASK_LIST.md)
