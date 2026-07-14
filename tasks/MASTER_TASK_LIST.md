# KiCad AI Integration — Master Task List

[Home](../README.md) › [Project Index](../PROJECT_INDEX.md) › Master Task List

> Phased implementation backlog for the Python-scripting API integration with AI,
> aligned to [Software Architecture](../docs/Architecture/KiCad_AI_Integration_Software_Architecture.md)
> and [README](../README.md).

**Current repository status:** Planning / documentation only — no `src/` code yet.

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
- [ ] Add package `__init__.py` files and a minimal importable package layout

### KiCad compatibility & dev workflow

- [ ] Target KiCad 8+; document minimum supported version in README
- [ ] Confirm availability of `pcbnew`, schematic access, and `wxPython` inside KiCad
- [ ] Document how to run code inside KiCad (Scripting Console vs external plugin action)
- [ ] Define strategy for testing outside KiCad (mock `pcbnew` objects, file-based fixtures)
- [ ] Add a minimal sample KiCad project under `examples/` for integration testing

### Configuration

- [ ] Define configuration schema (API keys, provider profile, model selection)
- [ ] Support API key via environment variable (e.g. `ANTHROPIC_API_KEY`)
- [ ] Support optional local config file for user preferences
- [ ] Never hardcode credentials in source or committed files

### Security baseline

- [ ] Require explicit user approval before any cloud API transmission
- [ ] Provide a context preview so users can see what will be sent
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

- [ ] Extract component references, values, and footprints
- [ ] Extract pin connections and net labels
- [ ] Extract schematic hierarchy (sheets, subsheets)
- [ ] Extract custom component fields (e.g. `Datasheet`, `Vds_max`)

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

- [ ] Export or parse netlist (SPICE or OrcadPCB2 format)
- [ ] Build connectivity graph / critical-node map — [kicad_ai_prep pattern](../docs/Developer_Handbook/Guide-Programmatic_AI_Analysis.md)

#### BOM

- [ ] Extract bill of materials with component attributes
- [ ] Include custom fields relevant to AI review (datasheet URLs, ratings)

#### ERC / DRC

- [ ] Gather ERC violation results (run or read existing report)
- [ ] Gather DRC violation results (run or read existing report)

#### Optional (Phase 1 stretch)

- [ ] Extract currently selected schematic/PCB objects as focused context
- [ ] Accept optional external firmware file path (e.g. Pico `main.py`) for cross-review

### 1.2 Project Context Model

- [ ] Define `ProjectContext` schema (dataclass or typed dict)
- [ ] Include: metadata, components, nets, footprints, board_stats, constraints, bom, erc_results, drc_results
- [ ] Support optional `user_description` (design intent text) and `selection` context
- [ ] Serialize to JSON for prompt assembly and debugging
- [ ] Support partial context flags (e.g. PCB-only, schematic-only, critical-nets-only)
- [ ] Design for token budgeting (summarization hooks, size estimation)

### 1.3 Prompt Builder

- [ ] Implement template system with named engineering audit templates
- [ ] General design review template
- [ ] PCB layout / trace audit template
- [ ] Isolation and clearance audit template
- [ ] Netlist-vs-visual cross-reference template — [AI Tools guide](../docs/Reference/AI_Tools_for_Advanced_Circuit_Analysis.md)
- [ ] Use structured XML-style sections: `<functional_description>`, `<kicad_python_extracted_data>`, `<kicad_netlist>`, `<pico_firmware>`, etc.
- [ ] Append user natural-language question to structured context
- [ ] Token optimization: summarize large nets, omit S-expression noise, chunk oversized payloads
- [ ] Configurable system-role persona per template (power electronics, embedded, general)

### 1.4 AI Provider Layer

- [ ] Define abstract provider interface: `send_message(prompt, config) -> response`
- [ ] Implement Claude 3.5 Sonnet provider (Anthropic Messages API)
- [ ] Use correct endpoint: `https://api.anthropic.com/v1/messages`
- [ ] Use model ID: `claude-3-5-sonnet-20241022` (or current Sonnet 3.5 identifier)
- [ ] Handle API errors: auth failure, rate limits, timeouts, malformed responses
- [ ] Parse `content[]` blocks from API response
- [ ] Return token usage metadata (input/output counts) for future Phase 2 display
- [ ] Design provider enum and config for future providers (OpenAI, Gemini, Ollama, etc.)

### 1.5 KiCad User Interface (wxPython)

Based on [Direct Claude API Chat guide](../docs/Developer_Handbook/Guide-In_KiCad_Claude_Chat_Integration.md), extended for production use.

- [ ] wxPython dialog with password-masked API key field (load from env/config if set)
- [ ] Context inclusion checkboxes: schematic, PCB, BOM, ERC, DRC, netlist, firmware
- [ ] Optional design-intent / functional-description textarea
- [ ] User prompt input field and Send button
- [ ] Context preview panel showing payload summary before transmission
- [ ] Explicit Approve & Send step (security requirement)
- [ ] Read-only response display area
- [ ] Status bar or inline messages for errors and connection status
- [ ] Entry-point script runnable from KiCad Scripting Console (`scripts/run_ai_assistant.py`)

### 1.6 Integration, Tests & Examples

#### Unit tests

- [ ] Context model serialization / deserialization
- [ ] Prompt assembly from fixtures (golden-file snapshots)
- [ ] Provider layer with mocked HTTP responses

#### Integration tests

- [ ] File-based fixtures: sample `.kicad_sch`, `.kicad_pcb`, netlist files
- [ ] End-to-end pipeline: fixture → context → prompt → mocked provider response

#### Manual E2E validation

- [ ] Open KiCad PCB Editor → run script → ask engineering question → receive Claude response
- [ ] Verify no manual export or browser copy-paste required

#### Reference example

- [ ] Add `examples/bedini_babcock/` sample project (or equivalent test project)
- [ ] Include pre-built prompt template for flyback recovery audit
- [ ] Document expected inputs and sample questions for manual validation

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

### Dockable chat window

- [ ] Persistent wx panel dockable alongside schematic/PCB editor
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

**Phase 2 exit criteria:** Dockable in-editor chat with conversation history, template
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
- [ ] Datasheet analysis (BOM field links, optional text/PDF ingestion)
- [ ] Circuit explanation mode (topology walkthrough from schematic context)

### Code & simulation generation

- [ ] KiCad Python script generation from AI responses (with validation sandbox)
- [ ] SPICE simulation assistance (netlist export + template prompts)
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

- [ ] User install and setup guide (API key, KiCad version, first run)
- [ ] Developer guide (repo layout, running tests, adding extractors/providers)
- [ ] Architecture docs: Prompt Architecture, AI Provider Interface, Roadmap
- [ ] Keep README current status section updated per phase completion

### Security

- [ ] Audit credential storage approach
- [ ] Context redaction options (exclude paths, obfuscate project name)
- [ ] Local-model path for air-gapped / privacy-sensitive workflows (Ollama, etc.)
- [ ] Document what data leaves the machine on each request

### Testing & CI

- [ ] pytest suite runnable without KiCad installed
- [ ] Mock `pcbnew` for unit tests
- [ ] Golden-file prompt snapshots to catch regressions
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

## Architecture Component Mapping

| Architecture component | Primary phase | Key deliverable |
|------------------------|---------------|-----------------|
| Context Collection Engine | Phase 1 | `src/context/` extractors |
| Project Context Model | Phase 1 | `src/context/model.py` (or equivalent) |
| Prompt Builder | Phase 1 | `src/prompts/` templates + builder |
| AI Provider Layer | Phase 1 | `src/providers/` abstraction + Claude impl |
| KiCad User Interface | Phase 1 → 2 | `src/ui/` dialog → dockable plugin |
| Conversation Manager | Phase 2 | `src/` session/history module |

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
