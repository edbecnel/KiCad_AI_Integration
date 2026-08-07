# KiCad AI Integration — Master Task List

[Home](../README.md) › [Project Index](../PROJECT_INDEX.md) › Master Task List

> **Status:** Maintained
> **Owner:** Project maintainers
> **Applies To:** KiCad AI Integration implementation tracking
> **Last Reviewed:** 2026-08-07
> **Review Frequency:** Monthly

> Phased implementation backlog for the Python-scripting API integration with AI,
> aligned to [Software Architecture](../docs/Architecture/KiCad_AI_Integration_Software_Architecture.md)
> and [README](../README.md).

**Current repository status:** Phase 1 stretch slice + platform Tracks B–D complete. **Working:** launcher (`--ui`), schematic context + datasheet library, chat UI with Approve & Send (`--ui-chat`), simulation/SUBCKT panel (`--ui-simulation`), built-in sim model auto-apply, AERF staged analysis (`--ui-aerf`), Engineering Notebook (`--ui-notebook`), EKM runtime + AERF write-back. **Still open:** full PCB extraction (tracks/vias/zones/net classes), BOM/ERC/DRC in context, additional prompt templates, native KiCad plugin, unified Assistant shell (ADP-011).

**Primary goal:** Build an in-KiCad AI engineering assistant that automatically gathers
project context, constructs optimized prompts, calls Claude 3.5 Sonnet, and displays
responses — minimizing manual export and copy-paste workflows.

**Reference use case:** The Bedini/Babcock flyback recovery examples in the architecture
guides are validation scenarios, not the project scope itself. See
[Appendix: Reference Example Workflow](#appendix-reference-example-workflow).

---

## Phase 0 — Foundation & Repository Scaffold

**Goal:** Establish the codebase structure, dev workflow, configuration, and security
baseline before feature work begins.

### Repository structure

- [x] Create `src/context/` — KiCad data extraction modules
- [x] Create `src/prompts/` — prompt templates and prompt builder
- [x] Create `src/providers/` — AI provider abstraction and implementations
- [x] Create `src/ui/` — wxPython user interface components
- [x] Create `src/utils/` — shared helpers (config, units, serialization)
- [x] Create `src/plugin/` — placeholder for Phase 2 native plugin entry points
- [x] Create `tests/` — unit and integration tests
- [x] Create `examples/` — sample projects and reference workflows
- [x] Create `scripts/` — KiCad-runnable entry-point scripts
- [x] Add package `__init__.py` files and a minimal importable package layout

### KiCad compatibility & dev workflow

- [x] Target KiCad 8+; document minimum supported version in README — see [ADR-0001](../docs/Architecture/ADRs/ADR-0001-KiCad-8-Minimum-Version.md)
- [ ] Confirm availability of `pcbnew`, schematic access, and `wxPython` inside KiCad
- [x] Document how to run code inside KiCad (Scripting Console vs external Terminal) — [Testing With Your KiCad Project](../docs/User_Guides/Testing_With_Your_KiCad_Project.md), [07_E2E_Full_Flow](../docs/Developer_Handbook/07_E2E_Full_Flow.md)
- [x] Define strategy for testing outside KiCad (mock `pcbnew` objects, file-based fixtures) — [05_Testing](../docs/Developer_Handbook/05_Testing.md), `tests/fixtures/`, [Testing With Your KiCad Project](../docs/User_Guides/Testing_With_Your_KiCad_Project.md)
- [x] File-based schematic fixtures under `tests/fixtures/` for integration testing

### Configuration

- [x] Define configuration schema (API keys, provider profile, model selection) — `src/utils/config.py`
- [x] Support API key via environment variable (e.g. `ANTHROPIC_API_KEY`)
- [x] Support optional local config file for user preferences
- [x] Config: `artifact_library_path` — shared library root for datasheets and libs (default `~/kicad_ai_library/`)
- [x] Config: `datasheet_search_paths` — local folders scanned for import into shared library
- [x] Never hardcode credentials in source or committed files

### Security baseline

- [ ] Require explicit user approval before any cloud API transmission — done for `--ui-chat`; `--ask` is dev bypass
- [x] Provide a context preview so users can see what will be sent — chat dialog
- [ ] Support selective context inclusion (user toggles per data type)
- [ ] Document data-handling and credential-storage practices

**Phase 0 exit criteria:** Repo scaffold exists, config schema defined, dev/test
instructions documented, security rules established.

---

## Phase 1 — Python Script MVP

**Goal:** A Python script runnable inside KiCad that performs a stateless, one-shot
AI request with automatic context collection. No persistent chat history.

Maps to architecture components: Context Collection Engine, Project Context Model,
Prompt Builder, AI Provider Layer, and initial KiCad UI (wxPython dialog).

### 1.1 Context Collection Engine

Extract structured data from the active KiCad project via `pcbnew` API and/or
S-expression file parsing.

#### Schematic (`.kicad_sch`)

- [x] Extract component references, values, and footprints — `src/context/schematic_parse.py`
- [ ] Extract pin connections and net labels — schematic labels via `schematic_connectivity.py` (pins TBD)
- [x] Extract schematic hierarchy (sheets, subsheets) — one-level subsheet walk
- [x] Extract custom component fields (e.g. `Datasheet`, `Vds_max`)

#### PCB (`pcbnew.GetBoard()`)

- [ ] Extract footprints (reference, value, position, layer)
- [ ] Extract tracks per net (width, length, layer) — [Script A pattern](../docs/Developer_Handbook/Guide-KiCad_Python_API_Custom_AI_Scripting.md)
- [ ] Extract vias and zones
- [ ] Extract net classes (clearance, track width rules) — [Script B pattern](../docs/Developer_Handbook/Guide-KiCad_Python_API_Custom_AI_Scripting.md)
- [ ] Extract board design settings and constraints
- [ ] Compute board statistics (layer usage, trace totals, etc.)

#### Project metadata

- [ ] Read project file for name, paths, and project-level settings
- [ ] Detect active schematic and PCB file paths from open editor context

#### Netlist

- [x] Export or parse netlist (SPICE via `kicad-cli`; summary in `ProjectContext.netlist_summary`) — `src/context/netlist_export.py` (OrcadPCB2 format TBD)
- [ ] Build connectivity graph / critical-node map — [kicad_ai_prep pattern](../docs/Developer_Handbook/Guide-Programmatic_AI_Analysis.md)

#### BOM

- [ ] Extract bill of materials with component attributes
- [ ] Include custom fields relevant to AI review (datasheet URLs, ratings)

#### ERC / DRC

- [ ] Gather ERC violation results (run or read existing report)
- [ ] Gather DRC violation results (run or read existing report)

#### Optional schematic image (Phase 1 stretch)

- [x] Document export pipeline — [ADR-0004](../docs/Architecture/ADRs/ADR-0004-Optional-Multimodal-Schematic-Context.md)
- [x] Implement `export_schematic_image(path, dpi=600, pages=None) -> bytes` in `src/context/schematic_image.py`
- [x] Resolve `kicad-cli` path (`KICAD_CLI` env var, `shutil.which`, macOS app bundle fallback)
- [x] Export via `kicad-cli sch export pdf --black-and-white --exclude-drawing-sheet`
- [x] Rasterize with `pdftoppm -png -r 600 -singlefile`
- [x] Detect KiCad 9+ native `sch export png --dpi` and prefer when available
- [ ] Check `pdftoppm` availability; surface clear UI error if Poppler is missing
- [ ] Prompt user to save project before export when schematic has unsaved edits
- [x] Extend `ProjectContext` with optional `schematic_image` and `schematic_image_meta`

#### Netlist gap-fill detection (Phase 1 stretch)

- [ ] Detect symbols with incomplete netlist connectivity — see [Netlist Gap Fill](../docs/Specifications/Netlist_Gap_Fill.md)
- [ ] Flag auto-generated net names (`Net-(…)`) and unconnected pins in context model
- [x] Detect symbols missing `Spice_Model` or unresolved `.include`/`.lib` references in exported SPICE netlist — `src/context/simulation_gaps.py`
- [x] **Shared artifact library:** create `artifact_library_path` with `catalog.json`, `datasheets/`, `libs/`; dedupe by `sha256`
- [x] **Per-project registry:** `kicad_ai/project_manifest.json` beside `.kicad_pro`; link to catalog entries
- [x] **Reference tracking:** update `referenced_by` in catalog (project, schematic path, sheet, component ref) on each scan
- [x] **Datasheet resolver:** read shared `catalog.json` and per-project `project_manifest.json`
- [x] **Datasheet resolver:** read symbol `Datasheet` field from `.kicad_sch`; import into shared library when not cataloged
- [x] **Datasheet resolver:** support user PDF attach/register per component; cache under project artifact store
- [x] **Datasheet resolver:** controlled `https:` fetch when symbol field is URL only (SSRF-safe, size/timeout limits, cache PDF)
- [x] **Datasheet resolver:** persistent `url_fetch_log.json` per part+URL (`downloaded` / `failed`); skip repeat fetches; set `needs_ai_datasheet_discovery` on failure
- [x] **AI datasheet discovery mode:** opt-in web search for official PDF URLs, auto-download, `ai_discovery_log.json`; on failure show URL + manual attach / `{Value}.pdf` instructions — see [AI Datasheet Discovery](../docs/Specifications/AI_Datasheet_Discovery.md)
- [x] **Per-part datasheet reset:** unlink manifest/catalog, clear `url_fetch_log`, quarantine `{Value}.pdf`, `force_refresh_parts` resolver bypass; **Datasheets** panel (Missing | All required) + `--reset-datasheet` CLI
- [ ] **Project-wide force refresh datasheets (UI):** re-fetch all symbol HTTPS URLs with full catalog/`url_fetch_log` bypass — **Force refresh URLs** today only retries failed URL fetches
- [x] **Catalog scan:** pick up new files in shared `datasheets/` — `ArtifactStore.scan_datasheets_folder()`
- [x] **CLI user notice:** print **Manual datasheets required** when auto-fetch fails for datasheet-required parts (`context/datasheet_requirements.py`)
- [x] SUBCKT routing: Tier A/B/C tier hints via `DatasheetResolution.tier_hint`; prompts in `src/prompts/templates/subckt.py`
- [x] Tier A: extract structured component facts from resolved PDF before `.SUBCKT` synthesis — `src/context/pdf_text.py`, `build_subckt_facts_prompt` (requires optional `pypdf`)
- [x] Tier B: include symbol pin list, fields, footprint, schematic context in prompt — `build_subckt_tier_b_prompt` (optional 600 DPI image in Tier B prompt TBD)
- [x] Emit `provenance.json` with datasheet path or `sources_used[]` per generated model — `src/context/subckt_generation.py`

#### Optional (Phase 1 stretch)

- [ ] Extract currently selected schematic/PCB objects as focused context
- [ ] Accept optional external firmware file path (e.g. Pico `main.py`) for cross-review

### 1.2 Project Context Model

- [x] Define `ProjectContext` schema (dataclass or typed dict) — stretch slice in `src/context/model.py`; implements `platform_core.DesignSnapshot`
- [x] Include project metadata and components — `project_name`, `schematics`, `symbols`
- [x] Include schematic connectivity (net labels) — `schematic_connectivity`
- [x] Include PCB summary (footprint/net counts) — `pcb_summary` via `src/context/pcb_summary.py`
- [x] Include SPICE netlist summary — `netlist_summary`
- [ ] Include: full nets, footprints, board_stats, constraints, bom, erc_results, drc_results
- [ ] Support optional `user_description` (design intent text) and `selection` context
- [x] Serialize to JSON for prompt assembly and debugging
- [ ] Support partial context flags (e.g. PCB-only, schematic-only, critical-nets-only)
- [ ] Design for token budgeting (summarization hooks, size estimation)
- [x] Include optional `schematic_image` and `schematic_image_meta` fields when multimodal context is enabled

### 1.3 Prompt Builder

- [x] Implement template system with named engineering audit templates — `src/prompts/builder.py`, `general_review`
- [x] General design review template — `src/prompts/templates/general_review.py`
- [ ] PCB layout / trace audit template
- [ ] Isolation and clearance audit template
- [ ] Netlist-vs-visual cross-reference template — [AI Tools guide](../docs/Reference/AI_Tools_for_Advanced_Circuit_Analysis.md)
- [ ] Netlist gap-fill template — connectivity inference and SUBCKT `.lib` generation — [Netlist Gap Fill spec](../docs/Specifications/Netlist_Gap_Fill.md) (SUBCKT templates exist; connectivity-inference template TBD)
- [x] SUBCKT Tier A two-stage prompts (PDF fact extraction, then model synthesis matched to KiCad pin order) — `src/prompts/templates/subckt.py`, `src/context/subckt_generation.py`
- [x] SUBCKT Tier B multi-source context prompt (symbol pins, fields, footprint, schematic context — no part-number-only)
- [x] SUBCKT Tier C last-resort prompt with mandatory `needs-manual-review` labeling
- [x] Use structured XML-style sections: `<functional_description>`, `<kicad_python_extracted_data>`, `<kicad_netlist>`, etc. — general review template
- [x] Append user natural-language question to structured context
- [x] Token optimization: compact symbol table for large schematics (>50 symbols) — `src/prompts/compact.py` (net/S-expression chunking TBD)
- [ ] Configurable system-role persona per template (power electronics, embedded, general)

### 1.4 AI Provider Layer

- [x] Define abstract provider interface: `send_message(prompt, config) -> response` — `src/providers/base.py`
- [x] Implement Claude 3.5 Sonnet provider (Anthropic Messages API) — `src/providers/claude.py`
- [x] Use correct endpoint: `https://api.anthropic.com/v1/messages`
- [x] Use model ID: `claude-3-5-sonnet-20241022` (or current Sonnet 3.5 identifier) — config `claude_model`
- [x] Handle API errors: auth failure, rate limits, timeouts, malformed responses — `src/providers/errors.py`
- [x] Parse `content[]` blocks from API response
- [x] Attach schematic image as multimodal `image` content block when `ProjectContext.schematic_image` is present
- [x] Return token usage metadata (input/output counts) for future Phase 2 display
- [x] Design provider enum and config for future providers (OpenAI, Gemini, Ollama, etc.) — `ProviderKind`, `ai_provider` config

### 1.4b Engineering Inference Engine (EIE)

- [x] EIE chat workflow — `src/inference/chat.py` (context → prompt → provider → response)
- [x] EIE simulation orchestration — `src/inference/simulation.py`
- [x] EIE AERF pipeline orchestration — `src/inference/aerf.py` (see Track C)

### 1.5 KiCad User Interface (wxPython)

Based on [Direct Claude API Chat guide](../docs/Developer_Handbook/Guide-In_KiCad_Claude_Chat_Integration.md), extended for production use.

- [x] wxPython dialog with password-masked API key field (load from env/config if set) — `src/ui/chat_dialog.py`
- [ ] Context inclusion checkboxes: schematic, PCB, BOM, ERC, DRC, netlist, firmware
- [x] "Include schematic image" checkbox (off by default; optional remember-last-choice) — chat dialog
- [x] Optional design-intent / functional-description textarea — chat dialog
- [x] User prompt input field and Send button — chat dialog (Approve & Send)
- [x] Context preview panel showing payload summary before transmission — chat dialog
- [x] **Missing required datasheets panel (wxPython)** — list + Attach PDF + Refresh — `src/ui/missing_datasheets_dialog.py`, `src/ui/launcher.py`
- [x] Per-component **Attach PDF** file picker — `attach_datasheet_pdf()` + `--ui-datasheets` on CLI
- [x] **Datasheet drag-and-drop UI** — drop PDF on selected row in Missing datasheets panel
- [x] Explicit Approve & Send step (security requirement) — chat dialog confirmation
- [x] Read-only response display area — chat dialog
- [x] Status bar or inline messages for errors and connection status — chat dialog status line
- [x] **Launcher dialog** — project picker, context summary, panel shortcuts — `src/ui/launcher_dialog.py`, `--ui`
- [x] **Simulation panel** — gap scan, SUBCKT generation, spice write-back — `--ui-simulation`, `src/ui/simulation_dialog.py`
- [x] **AERF staged analysis panel** — per-stage Approve & Send — `--ui-aerf`, `src/ui/aerf_dialog.py`
- [x] **Engineering Notebook UI** — modal and non-modal panel — `--ui-notebook`, `--ui-notebook-panel` (see Track D)
- [x] Entry-point script runnable from KiCad Scripting Console (`scripts/run_ai_assistant.py`) — `--ui`, `--ui-chat`, `--ui-datasheets`, `--ui-simulation`, `--ui-aerf`, `--ui-notebook`, `--ask`

### 1.6 Integration, Tests & Examples

#### Unit tests

- [x] Context model serialization / deserialization
- [x] Prompt assembly from fixtures (golden-file snapshots) — `tests/prompts/test_builder.py`
- [x] Provider layer with mocked HTTP responses — `tests/providers/test_claude_provider.py`

#### Integration tests

- [x] File-based fixtures: sample `.kicad_sch`, `.kicad_pcb`, netlist files — `tests/fixtures/`
- [x] Stretch pipeline: fixture → context → JSON summary — `tests/context/test_collector.py`
- [ ] End-to-end pipeline: fixture → context → prompt → mocked provider response

#### Manual E2E validation

Full-flow checklists: [Testing With Your KiCad Project](../docs/User_Guides/Testing_With_Your_KiCad_Project.md), [07_E2E_Full_Flow](../docs/Developer_Handbook/07_E2E_Full_Flow.md).

- [ ] Open KiCad PCB Editor → run script → ask engineering question → receive Claude response
- [ ] Verify no manual export or browser copy-paste required

#### Reference example

- [ ] Add `examples/bedini_babcock/` sample project (or equivalent test project)
- [ ] Include pre-built prompt template for flyback recovery audit
- [ ] Document expected inputs and sample questions for manual validation — see [Testing With Your KiCad Project](../docs/User_Guides/Testing_With_Your_KiCad_Project.md)

### 1.7 Simulation & SUBCKT pipeline

- [x] Simulation panel UI — `--ui-simulation`, gap scan, generate SUBCKT, write spice fields — `src/ui/simulation_dialog.py`
- [x] SUBCKT generation orchestration — tier routing, validation, artifact registration — `src/context/subckt_generation.py`
- [x] Spice field / KiCad 9+ sim write-back — `src/context/schematic_sim_write.py`, `src/context/schematic_write.py`
- [x] Built-in simulation model resolver — R/C/L/diodes, KiCad 10 passive fix — `src/context/builtin_sim_models.py`
- [x] Auto-apply built-in sim models on context refresh + Simulation panel **Apply built-in models** — `collector.py`, `simulation_dialog.py`
- [x] Datasheet discovery prompt template — `src/prompts/templates/datasheet_discovery.py`
- [x] Simulation gap summary in launcher — `summarize_simulation_gaps` in `launcher_dialog.py`

**Phase 1 exit criteria:** Engineer opens KiCad, runs one script, asks a design question,
reviews the context preview, approves transmission, and receives a context-aware Claude
response without manual export/copy-paste.

---

## Phase 2 — Native KiCad Plugin & Conversational UX

**Goal:** Evolve from console script to installable plugin with persistent, multi-turn chat.

### Plugin packaging

- [ ] Convert entry point to KiCad action plugin with toolbar/menu integration
- [ ] Document install path (`plugins/` directory) and update workflow
- [ ] Plugin metadata (name, description, icon, version)

### Dockable Assistant shell

- [ ] **Unified Assistant shell (tabbed UI, dual host)** — one window with shared header + Chat / Datasheets / Simulation / AERF / Notebook tabs; same component in Terminal `--ui` and KiCad dock — [ADP-011](../docs/Architecture/ADP-011-Assistant-Shell-UI.md)
- [ ] Persistent wx panel dockable alongside schematic/PCB editor (hosts `AssistantShell`)
- [ ] Non-blocking UI (API calls on background thread)
- [ ] Resize-friendly layout

### Conversation Manager

- [ ] Maintain multi-turn chat history within session
- [ ] Attach prior conversation turns to subsequent API requests
- [ ] Store prompt history for debugging and replay

### Incremental context

- [ ] Detect project changes between conversation turns
- [ ] Refresh only modified context layers instead of full re-extract every message

### Enhanced UX

- [ ] Markdown rendering in response pane (headers, lists, code blocks)
- [ ] Prompt template library (user-selectable from UI)
- [ ] Token usage display per request
- [ ] Cost estimation per model
- [ ] Context caching across conversation turns (static project data)

### Multi-provider support

- [ ] Provider profile switching in settings UI
- [ ] Implement at least one additional provider (e.g. OpenAI or Ollama) via abstraction layer
- [ ] Model selection per provider

**Phase 2 exit criteria:** Dockable in-editor Assistant shell with conversation history, template
library, token/cost visibility, and provider profile switching.

---

## Phase 3 — Advanced Engineering Assistant

**Goal:** Domain-specific audit workflows and interactive engineering capabilities
beyond free-form chat.

### Automated design review

- [ ] One-click schematic review action
- [ ] One-click PCB layout review action
- [ ] Structured review report output (findings, severity, recommendations)

### Domain-specific analysis

- [ ] Power integrity guidance (net class data, layer stackup, decoupling proximity)
- [ ] Signal integrity guidance (impedance rules, return paths)
- [ ] EMI/EMC recommendations (loop area, switching path length, isolation gaps)
- [ ] Design rule interpretation (DRC/ERC results explained in engineering terms)

### Component & datasheet intelligence

- [ ] Component comparison from BOM parametric data
- [x] Datasheet resolver for gap-fill — symbol `Datasheet` field, local paths, user registration, controlled URL fetch, `url_fetch_log.json` (see Phase 1 stretch; [Netlist Gap Fill](../docs/Specifications/Netlist_Gap_Fill.md))
- [x] AI-assisted datasheet discovery mode — web search, auto-download, failure URLs + manual fallback — [AI Datasheet Discovery](../docs/Specifications/AI_Datasheet_Discovery.md) (see Phase 1 stretch)
- [x] Per-part datasheet reset — selective hard refresh by Value; Datasheets panel + `--reset-datasheet` CLI (see [Netlist Gap Fill](../docs/Specifications/Netlist_Gap_Fill.md#per-part-datasheet-reset))
- [ ] Project-wide force refresh datasheets — re-download all HTTPS URLs with full catalog + failed-log bypass (partial: **Force refresh URLs** retries failed fetches only)
- [x] Datasheet text extraction from resolved PDFs for SUBCKT Tier A — `src/context/pdf_text.py` (see Phase 1 stretch Tier A)
- [ ] Circuit explanation mode (topology walkthrough from schematic context)

### Code & simulation generation

- [ ] KiCad Python script generation from AI responses (with validation sandbox)
- [x] SPICE simulation assistance (netlist export + SUBCKT generation + spice write-back) — partial: functional `--ui-simulation` panel; closed-loop sim validation TBD (ADP-006)
- [ ] Suggest alternative circuits or component substitutions

### Interactive engineering

- [ ] Project memory across sessions (engineering decisions, prior review findings)
- [ ] Clickable component references in AI responses (R1, U3 → highlight in KiCad)
- [ ] Image rendering for schematic snapshots in chat context

**Phase 3 exit criteria:** Domain-specific audit workflows runnable as one-click actions,
not only free-form chat.

---

## Cross-Cutting Work (All Phases)

### Documentation

- [x] User install and setup guide (API key, KiCad version, first run) — partial: [Testing With Your KiCad Project](../docs/User_Guides/Testing_With_Your_KiCad_Project.md), [00_First_Time_Setup](../docs/Developer_Handbook/00_First_Time_Setup.md)
- [x] Developer guide (repo layout, running tests, adding extractors/providers) — partial: [Developer Handbook](../docs/Developer_Handbook/README.md); contribution workflow TBD
- [x] Architecture docs: Prompt Architecture, AI Provider Interface, Roadmap
- [x] Feature Overview: KiCad host capabilities, platform scope, how-it-works, and gap summary — [Feature Overview](../docs/User_Guides/Feature_Overview.md) (authoritative scope reference)
- [x] [Custom Trifilar Coil Simulation Setup](../docs/User_Guides/Custom_Trifilar_Coil_Simulation_Setup.md) user guide
- [x] ADR-0010: AERP Platform Umbrella acronym — [ADR-0010](../docs/Architecture/ADRs/ADR-0010-AERP-Platform-Umbrella-Acronym.md)
- [x] ADP-006: Simulation abstraction (architecture) — [ADP-006](../docs/Architecture/ADP-006-Simulation-Abstraction.md); closed-loop implementation open
- [x] ADP-007: AERF prompt integration and EKM write-back — [ADP-007](../docs/Architecture/ADP-007-AERF-Prompt-Integration.md)
- [x] Keep README current status section updated per phase completion

### Security

- [ ] Audit credential storage approach
- [ ] Context redaction options (exclude paths, obfuscate project name)
- [ ] Local-model path for air-gapped / privacy-sensitive workflows (Ollama, etc.)
- [ ] Document what data leaves the machine on each request

### Testing & CI

- [x] pytest suite runnable without KiCad installed
- [ ] Mock `pcbnew` for unit tests
- [x] Golden-file prompt snapshots to catch regressions — `tests/prompts/golden/`, `tests/context/golden/`
- [ ] CI pipeline: lint + unit tests (optional KiCad-in-Docker for integration)

### Project housekeeping

- [ ] Resolve license (currently TBD in README)
- [ ] Contribution guidelines (coding standards, PR workflow, test requirements)
- [ ] `.gitignore` coverage for config files with secrets, generated artifacts

---

## Implementation Order (Phase 1 Critical Path)

```
Phase 0: Repo scaffold + config
    ↓
Context Collection Engine (PCB first)
    ↓
Project Context Model
    ↓
Prompt Builder ←── AI Provider Layer
    ↓                    ↓
    └──→ wxPython UI ←───┘
              ↓
        E2E test in KiCad
              ↓
    Phase 2: Plugin → Phase 3: Advanced audits
```

### Recommended first sprint (smallest useful slice)

1. PCB-only context extractor (tracks, nets, net classes)
2. JSON `ProjectContext` model
3. Single prompt template (PCB layout audit)
4. Claude provider with mocked unit tests
5. Minimal wxPython dialog (API key, question, response, send)
6. Manual test in KiCad PCB Editor

Then iteratively add schematic, BOM, ERC/DRC, netlist, context toggles, and preview/approve flow.

---

## Track B — Platform Frameworks (complete)

**Goal:** Implement host-independent platform layers per [Platform Architecture](../docs/Architecture/Platform_Architecture.md). Scope reference: [Feature Overview](../docs/User_Guides/Feature_Overview.md).

### Standing documentation checklist (each milestone)

- [x] Update [Feature Overview](../docs/User_Guides/Feature_Overview.md) platform gaps table
- [x] Check off items in this section
- [x] Update [Platform Architecture](../docs/Architecture/Platform_Architecture.md) implementation status
- [x] Update [ADP-010](../docs/Architecture/ADP-010-Engineering-Inference-Engine.md) §8 when EIE changes
- [x] Run `pytest` (platform tests must not require KiCad/wx)

### Phase B1 — EKM runtime + CLI

- [x] `src/ekm/` — model, io, validate, paths, errors
- [x] `scripts/ekm_tool.py` — validate, init, show
- [x] `tests/ekm/`

### Phase B2 — AERF reasoning registry

- [x] `src/reasoning/` — stages, kb_loader, family_registry
- [x] `docs/Engineering_Knowledge/Circuit_Families/families.json`
- [x] `tests/reasoning/`

### Phase B3 — Blocking Oscillator KB

- [x] Rename `Blocking_Oscilllator/` → `Blocking_Oscillator/` (done)
- [x] Stage files 02–07 with family-specific content
- [x] Breadcrumbs and registry status → Complete

### Phase B4 — EIE expansion

- [x] Migrate simulation workflow to `src/inference/simulation.py`
- [x] `src/inference/aerf.py` — stage-0 dry-run stub
- [x] `tests/inference/` simulation + aerf tests

---

## Track C — AERF + EIE depth (complete)

**Goal:** Full staged AERF orchestration with circuit-family classification, per-stage prompts, approval-gated pipeline, and EKM write-back. See [Feature Overview](../docs/User_Guides/Feature_Overview.md) Part 4.

### Standing documentation checklist (each milestone)

- [x] Update [Feature Overview](../docs/User_Guides/Feature_Overview.md) platform gaps table
- [x] Check off items in this section
- [x] Update [ADP-010](../docs/Architecture/ADP-010-Engineering-Inference-Engine.md) §8 when EIE changes
- [x] Run `pytest` (platform tests must not require KiCad/wx)

### Phase C1 — Circuit family classifier

- [x] `src/reasoning/classifier.py` — classify `DesignSnapshot` against circuit-family KB

### Phase C2 — AERF stage prompts

- [x] Per-stage prompt templates — `src/prompts/templates/aerf_stage.py`

### Phase C3 — AERF pipeline

- [x] Multi-stage orchestration with approval gating — `run_aerf_pipeline`, `--approve-send`, `--ui-aerf`

### Phase C4 — EKM write-back

- [x] Map approved stage outputs to EKM sections — `src/ekm/aerf_writeback.py`, `--approve-ekm-writeback`, AERF UI **Write to EKM**

### Platform contracts

- [x] `platform_core.DesignSnapshot` protocol — `src/platform_core/contracts.py`
- [ ] `HostLink` generalization beyond `KiCadLink` — deferred until second host ([ADP-009](../docs/Architecture/ADP-009-Host-Integration-Layer.md) §8–9)

---

## AERF — AI Engineering Reasoning Framework

**Goal:** Establish staged engineering reasoning as a foundational architectural pillar. See [ADP-008](../docs/Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md) and [ADR-0007](../docs/Architecture/ADRs/ADR-0007-AERF-Foundation.md).

### Milestone 1 — Architecture formalization (complete)

- [x] ADP-008: AERF Foundation specification
- [x] ADR-0007: Ratify AERF as architectural pillar
- [x] EDF domain scaffold: `docs/Engineering_Knowledge/`
- [x] AERF Stage Index and Circuit Families registry
- [x] Navigation integration (PROJECT_INDEX, EDF, Architecture indexes)

### Next milestone — Reference circuit family KB

- [x] Blocking Oscillator as first circuit family (`docs/Engineering_Knowledge/Circuit_Families/Blocking_Oscillator/`)
- [x] Stage files 00–07 with family-specific content

### Future implementation

- [x] `src/reasoning/` orchestrator module (stage registry + KB loader; full LLM orchestration deferred)
- [x] Circuit family classifier
- [x] Per-stage prompt templates (ADP-007)
- [x] EKM stage-output mapping and write-back (ADP-007) — `src/ekm/aerf_writeback.py`
- [ ] Simulation closed loop — validate/refine stages (ADP-006)
- [x] AERF multi-stage orchestration with approval gating (`run_aerf_pipeline`, CLI, `--ui-aerf`)
- [x] AERF UI mode in chat or dedicated analysis panel (`src/ui/aerf_dialog.py`)

**AERF exit criteria:** Engineer runs staged analysis on a sample schematic; each stage produces reviewable JSON; approved Stage 7 conclusions write to EKM (`write_aerf_stages_to_ekm`, `--approve-ekm-writeback`, AERF UI). **Signed off** Aug 2026 — Bedini `Bedini_SSG_Radiant_Oscillator` via `tests/integration/test_bedini_aerf_exit.py` (collect, dry-run pipeline, mock 0–7 + writeback plan, chat prompt smoke).

### Track D — Engineering Notebook (ADP-003)

- [x] EKM View Model (`src/ekm/view_model.py`) — load, validate, edit, save, search
- [x] Field-type registry (`src/ekm/field_registry.py`) — all six EKM primitives
- [x] Notebook renderer (`src/ui/notebook_renderer.py`) — collapsible sections, registry-driven editors
- [x] Engineering Notebook UI — modal (`--ui-notebook`) and non-modal (`--ui-notebook-panel`)
- [x] Advanced JSON view tab (debug)
- [ ] Dockable KiCad action plugin shell (Phase 2; widget ready in `src/ui/notebook_panel.py`)

---

## Architecture Component Mapping

| Architecture component | Primary phase | Key deliverable |
|------------------------|---------------|-----------------|
| Context Collection Engine | Phase 1 | `src/context/` extractors |
| Project Context Model | Phase 1 | `src/context/model.py` (or equivalent) |
| Prompt Builder | Phase 1 | `src/prompts/` templates + builder |
| AI Provider Layer | Phase 1 | `src/providers/` abstraction + Claude impl |
| KiCad User Interface | Phase 1 → 2 | `src/ui/` dialogs → unified Assistant shell ([ADP-011](../docs/Architecture/ADP-011-Assistant-Shell-UI.md)) + dockable plugin |
| Conversation Manager | Phase 2 | `src/` session/history module |
| AERF Orchestrator | Track C (complete) | `src/reasoning/`, `src/inference/aerf.py` staged analysis pipeline |

---

## Out of Scope / Reference Only

These are documented alternatives, not the primary build path for this project:

- **K-AI Plugin** — community plugin; reference for UX patterns only
- **KiCad MCP Server** — external MCP approach; different architecture
- **Manual browser workflow** — export PNG, paste netlist into Claude web UI; replaced by in-KiCad automation
- **Obsidian** — personal documentation tooling; not part of project architecture

---

## Appendix: Reference Example Workflow

Validation scenario based on the Bedini/Babcock flyback recovery guides. Use to test
Phase 1 end-to-end, not as the product definition.

### Setup

- [ ] Sample project with labeled nets (`HV_Flyback`, `Coil_Plus`, `PICO_GPIO15`, etc.)
- [ ] Raspberry Pi Pico firmware stub for timing/isolation cross-review
- [ ] Design intent text: switching frequency, voltage targets, isolation requirements

### Automated pipeline test (replaces manual copy-paste)

- [ ] Run context extractor on sample project → verify JSON output
- [ ] Select "isolation and clearance audit" prompt template
- [ ] Ask: verify optocoupler isolation between Pico GPIO and HV switching loops
- [ ] Review AI response for: trace EM capacity, creepage/clearance, switching path length

### Manual checks the AI should catch (acceptance criteria)

- [ ] Netlist vs schematic consistency for flyback diodes and switching transistors
- [ ] Firmware timing vs netlist for GPIO isolation and dead-time
- [ ] Component stress analysis for transistor/diode Vds and transient ratings
