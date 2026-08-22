# KiCad AI Integration — Feature Overview

[Home](../../README.md) · [Project Index](../../PROJECT_INDEX.md) · [User Guides](README.md)

For project philosophy and how staged analysis works, see [Project Overview](../../PROJECT_OVERVIEW.md) and [How AERF Works](How_AERF_Works.md). For full architecture, see [Platform Architecture](../Architecture/Platform_Architecture.md).

---

## Part 1 — Introduction

### What this project is

This repository implements an **AI-assisted Electrical Engineering Reasoning Platform** — a set of reusable frameworks for structured engineering knowledge, staged reasoning, and AI-assisted inference.

**KiCad AI Integration** is the **first host product**: it brings those capabilities into KiCad so engineers can ask design questions against the **actual project** (schematic, parts, datasheets) instead of copying files into a generic chatbot.

| Lens | What you get |
|------|----------------|
| **KiCad user today** | Schematic-aware AI chat, datasheet management, early simulation/SUBCKT tooling — run from a script alongside KiCad |
| **Platform (longer term)** | Host-independent reasoning (EKM, AERF, EIE, prompts, providers) usable from other EDA tools, CLI, web, or lab software |

**Status:** Early working prototype on the KiCad host. Platform frameworks (EKM, AERF, EIE) are implemented; KiCad host Phase 1 file-based close-out is complete. Phase 2 productization (native plugin, embedded tabs) is next.

### Separation principle

**Platform frameworks must not depend on KiCad.** KiCad file parsers, `kicad-cli`, wxPython UI, and `kicad_ai/` paths are **host integration** concerns only. Reasoning, prompts, providers, and future EKM/AERF orchestration are designed to run without any KiCad installation.

---

## Part 2 — KiCad Host: What Works Today

Launch panels via [`scripts/run_ai_assistant.py`](../../scripts/run_ai_assistant.py) — recommended: `python scripts/run_ai_assistant.py --ui` (project picker and context refresh). See [Testing With Your KiCad Project](Testing_With_Your_KiCad_Project.md).

### Working now

#### Project understanding (schematic)
- Reads the open KiCad project schematic: components, values, footprints, references, hierarchy
- Builds structured context for AI review (not a raw file dump)

#### Datasheet management (`--ui-datasheets`)
- Shared library for datasheet PDFs across projects (`~/kicad_ai_library/`)
- Automatic resolution when PDFs exist or HTTPS URLs can be fetched
- **Datasheets** panel: **Missing** and **All required** tabs; attach files, drag-and-drop, refresh, **Reset & re-resolve** per part Value
- **Use AI to find datasheets** — opt-in URL suggestion when HTTPS fetch fails (`--ai-datasheets`; approval before download unless `--ai-datasheets-auto-fetch`)
- Catalog picks up manually added PDFs in the library folder
- CLI: `--reset-datasheet VALUE` for per-part hard refresh

#### AI integration (`--ui-chat`, `--ui-aerf`, `--ui-notebook`, `--ask` dev only)
- **Claude API** integration (model configurable, e.g. Sonnet 4.5)
- **Prompt builder** for general schematic design review (first template)
- Large schematics are summarized automatically so requests stay manageable
- Chat workflow runs through the platform **Engineering Inference Engine (EIE)** (`src/inference/`)

#### User interface (today)

`--ui` opens the **Assistant shell** ([ADP-011](../Architecture/ADP-011-Assistant-Shell-UI.md)): shared project header, tab bar, and **Refresh context**. Each tab opens the existing feature panel (Chat, Datasheets, Simulation, AERF, Notebook). You can also launch panels directly:

- **Chat** (`--ui-chat` or shell **Chat** tab): ask questions, **approve before sending**, read Claude's answer and token usage
- **Datasheets** (`--ui-datasheets` or launcher **Datasheets** button): attach PDFs, AI discovery, reset links — **not available inside Chat**
- **Simulation** (`--ui-simulation`): gap scan, SUBCKT generation, spice write-back
- **AERF** (`--ui-aerf`): staged circuit analysis with per-stage Approve & Send and optional EKM write-back
- **Engineering Notebook** (`--ui-notebook`, `--ui-notebook-panel`): view/edit EKM fields; search; Advanced JSON tab

**Known limitation:** Launcher and Chat both use the window title **"KiCad AI Assistant"**, so the launcher is easy to miss when Chat is open. For datasheet attach, use **Datasheets** or `--ui-datasheets` directly — see [Testing With Your KiCad Project](Testing_With_Your_KiCad_Project.md).

Runs from a terminal or KiCad Scripting Console (no native KiCad menu plugin yet). Optional **schematic image** for visual questions (`--image`; large designs are slow and costly — text Q&A is the reliable path today).

#### Assistant shell (Phase 1 scaffold)

The unified **Assistant shell** (`--ui`) provides a shared project header and tab bar; each tab opens the existing modal panel for Chat, Datasheets, Simulation, AERF, or Notebook. Fully embedded tab UIs and KiCad dockable hosting are Phase 2 — see [ADP-011](../Architecture/ADP-011-Assistant-Shell-UI.md).

#### Security / control
- Context **preview** before any cloud send (chat UI)
- **Approve & Send** gate in the chat UI (no silent upload of project data)
- `--ask` bypasses approval — **internal testing only**

### Partially working / early

| Feature | State |
|---------|--------|
| Schematic image (multimodal) | Implemented; best for smaller scopes or lower resolution |
| Net labels from schematic | Basic label extraction |
| PCB summary | Footprint/net counts plus tracks, vias, zones, net classes when PCB present |
| BOM summary | Value/footprint roll-up in `ProjectContext` |
| ERC / DRC reports | Included when report files exist beside the project |
| Chat context toggles | Include schematic, PCB, BOM, ERC/DRC, netlist per question |
| Chat audit templates | General review, PCB layout, isolation/clearance, netlist crosscheck (template selector in `--ui-chat`) |
| Netlist export | Via `kicad-cli` when available |
| **Simulation / SUBCKT panel** (`--ui-simulation`) | Gap scan, AI SUBCKT generation, spice field write-back to schematic — functional but not production-complete |
| Netlist gap-fill / SUBCKT | Gap detection + connectivity-inference template in chat; SUBCKT Tier A/B/C pipeline implemented — see [Netlist Gap Fill](../Specifications/Netlist_Gap_Fill.md) |
| Developer `--ask` shortcut | Works but bypasses approval UI — internal testing only |

### Not built yet (KiCad host — Phase 1 still open)

#### Richer project context
- Live ERC/DRC from KiCad API (today: scan saved report files only) — **Phase 1.5**
- Pin-level connectivity from schematic geometry (today: pin lists + netlist graph when exported)

#### More AI capabilities (KiCad host)
- Project-wide **force refresh datasheets** — **Force refresh all URLs** button re-fetches HTTPS symbol URLs with catalog bypass

#### Product polish (KiCad host)
- **Embedded tab UIs** and KiCad dockable Assistant shell (Phase 2) — [ADP-011](../Architecture/ADP-011-Assistant-Shell-UI.md)
- **Native KiCad plugin** (menu/toolbar entry, no separate terminal)
- Context preview **thumbnail** for schematic images
- **Multi-turn** conversation (history across questions)
- Token/cost display in a user-friendly way

### What you can demo today

An engineer can open a real KiCad project, launch the chat panel (`--ui-chat`), ask *"What are the main active parts on this schematic?"* or *"Which parts are missing datasheets?"*, review what will be sent, approve it, and get a **schematic-aware** answer from Claude — without exporting or copy-pasting.

The **datasheet workflow** is usable: identify missing PDFs, attach them, reset stale links per part Value, and refresh until resolved.

The **simulation panel** (`--ui-simulation`) can scan for missing SPICE models, generate SUBCKT libraries for selected parts, and write spice fields back to the schematic (user must revert/reload in KiCad editor after file write-back).

---

## Part 3 — Platform & How It Works

Architecture details live in [Platform Architecture](../Architecture/Platform_Architecture.md). This section answers the main **How** questions in plain language.

### How is KiCad separated from the framework?

| Layer | KiCad-dependent? | What it is |
|-------|------------------|------------|
| **Platform frameworks** | **No** | EKM, AERF, EIE, Prompt Architecture, AI Provider Layer, Artifact Library, Engineering Knowledge Libraries |
| **Host Integration (KiCad)** | **Yes** | Schematic/PCB parsers, `kicad-cli`, wxPython UI, `kicad_ai/` paths, schematic write-back, `ProjectContext` population |

**Dependency rule:** Platform modules (`providers/`, `prompts/`, `platform_core/`, `ekm/`, `reasoning/`, `inference/`) **must not** import KiCad parsers (`context/schematic_*`, `context/pcb_*`), `pcbnew`, or wxPython. Host modules may call into platform code. See [Developer Handbook — Platform import boundaries](../Developer_Handbook/README.md#platform-import-boundaries).

Ratified in [ADR-0009](../Architecture/ADRs/ADR-0009-Platform-Architecture-Foundation.md).

### How does a request flow through the system?

**KiCad path today:**

```
KiCad project files (.kicad_sch, .kicad_pcb, …)
  → Host: context collection → ProjectContext (DesignSnapshot)
  → Platform: EIE → prompt builder → AI provider
  → Host: wx UI displays response (Approve & Send gate)
```

**Planned staged reasoning path (implemented — see [Testing With Your KiCad Project](Testing_With_Your_KiCad_Project.md)):**

```
DesignSnapshot + EKM + Circuit Family KB
  → EIE runs AERF stages 0–7
  → user approval per stage or batch
  → curated conclusions written to EKM
```

### How is knowledge organized?

| Store | Role | KiCad-specific? |
|-------|------|-----------------|
| Host design files | Electrical connectivity (source of truth) | Yes for KiCad (`.kicad_sch`, netlist) |
| `DesignSnapshot` / `ProjectContext` | Extracted facts — what the design **is** | Population is KiCad-specific; [contract](../Architecture/ADP-009-Host-Integration-Layer.md) is not |
| **EKM** | Authored knowledge — why the design **is this way** | Schema uses `KiCadLink` today; model is host-agnostic — [ADP-001](../Architecture/ADP-001-Engineering-Knowledge-Model-Foundation.md) |
| **AERF** stage outputs | Transient per-analysis reasoning | No — [ADP-008](../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md) |
| **Circuit Family KB** | Reusable reference knowledge | No — [`docs/Engineering_Knowledge/`](../Engineering_Knowledge/README.md) |
| Conversations | Raw chat input (not canonical memory) | No (planned Phase 2) |
| Artifact library | Datasheets, SPICE libs, exports | No (content-addressed store) |

Conversations are **input**; EKM is **distilled output** after user approval.

### How do the frameworks relate?

| Framework | How it works | Status |
|-----------|--------------|--------|
| **AERF** | Defines *what* to reason about — eight stages (0–7), circuit-family overlays, methodology | Stage registry + KB loader in `src/reasoning/` — [ADP-008](../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md) |
| **EIE** | Defines *how* reasoning runs — orchestration, prompt assembly, provider calls, approval gating | Chat + simulation + AERF pipeline in `src/inference/`; `--ui-aerf` panel — [ADP-010](../Architecture/ADP-010-Engineering-Inference-Engine.md) |
| **EKM** | Persistent per-project engineering notebook (sections, typed fields, links) | Runtime + CLI in `src/ekm/`; Notebook UI (`--ui-notebook`) — [ADP-002](../Architecture/ADP-002-EKM-Schema-and-Persistence.md) |
| **Prompt Architecture** | Turns `DesignSnapshot` into structured prompts; no KiCad API imports | Implemented — [Prompt Architecture](../Architecture/Prompt_Architecture.md) |
| **AI Provider Layer** | Abstract LLM interface (Claude today) | Implemented — [ADR-0002](../Architecture/ADRs/ADR-0002-Provider-Abstraction-Layer.md) |
| **Engineering Notebook UI** | Human-facing EKM editor in KiCad | Implemented — [ADP-003](../Architecture/ADP-003-Engineering-Notebook-User-Interface.md) |

**AERF is a framework within the platform, not the platform itself.**

### How would another host integrate?

A new host (CLI, web, second EDA tool, lab software) implements five responsibilities defined in [ADP-009](../Architecture/ADP-009-Host-Integration-Layer.md):

1. **Context collection** → `DesignSnapshot`
2. **UI shell** (optional) — present results; enforce approve-before-send
3. **Artifact root** — per-project directory for manifests and exports (KiCad: `<project>/kicad_ai/`)
4. **Object linking** — EKM references to host objects (KiCad: `KiCadLink`)
5. **Write-back** (optional) — apply approved changes to host design files

All platform frameworks above that line are reused unchanged.

### Current code layout (transitional)

Physical directories do not yet mirror logical layers. Known tensions:

| Location | Logical layer | Note |
|----------|---------------|------|
| `src/providers/`, `src/prompts/`, `src/inference/` | Platform | No KiCad imports |
| `src/platform_core/contracts.py` | Platform | `DesignSnapshot` protocol |
| `src/context/artifacts/` | Platform | Content-addressed store; path may move later |
| `src/context/model.py` | Shared contract | `ProjectContext` implements `DesignSnapshot`; KiCad-shaped fields |
| `src/context/*parse*`, `src/ui/` | KiCad host | Parsers, wx UI; `simulation_supply.py` re-exports from `inference/simulation.py` |
| `kicad_ai/` on disk | KiCad host | Other hosts will use their own artifact root names |

Physical `src/hosts/kicad/` reorganization is deferred until a second host is actively developed.

---

## Part 4 — Roadmap, Gaps, and Bottom Line

### KiCad host roadmap

**Phase 2 — Plugin & conversational UX**
- Installable KiCad plugin, dockable chat window
- Conversation Manager (session history) — platform component, KiCad UI shell
- Markdown rendering, template library, multi-provider profiles

**Phase 3 — Engineering assistant (KiCad UX + platform reasoning)**
- One-click schematic and PCB audits
- Power/signal integrity and EMC guidance
- Staged circuit analysis via **AERF** with **EKM** write-back after approval
- Engineering Notebook UI for curated project knowledge

### Platform gaps (not KiCad-specific)

| Framework | Status | Next step |
|-----------|--------|-----------|
| EKM runtime (`src/ekm/`) | View Model + field registry + write-back | Phase 2 dockable plugin shell |
| AERF orchestrator (`src/reasoning/`) | Stage registry + KB loader + classifier + enriched prompts/validation | Additional circuit families |
| EIE (`src/inference/`) | Chat + simulation + AERF pipeline + EKM write-back | Notebook AI edit proposals |
| Engineering Notebook UI | Full primitive editors, search, JSON view (`--ui-notebook`) | Dockable KiCad plugin (Phase 2) |
| Conversation Manager | Deferred Phase 2 | Multi-turn transcripts |
| Simulation abstraction | [ADP-006](../Architecture/ADP-006-Simulation-Abstraction.md) | Host-agnostic validation hooks; closed loop deferred |
| Blocking Oscillator KB | Complete (00–07); **live AERF sign-off** (Bedini API run Aug 2026; fixtures + rubric) | Additional circuit families |

### Bottom line

| | |
|---|---|
| **KiCad host (proven)** | Schematic-aware AI Q&A with approval; datasheet library; simulation/SUBCKT panel; PCB/BOM/ERC/DRC context; Assistant shell scaffold |
| **Platform (foundation laid)** | EKM runtime + CLI; AERF classifier + prompts + pipeline + write-back + **learning loop** (EKM reload, library promotion); EIE chat/simulation/AERF UI; Blocking Oscillator KB |
| **In progress** | Phase 2 dockable plugin, simulation closed loop |
| **Later** | Native plugin, additional hosts, conversation persistence via EKM |

This is a **foundation**, not a finished product. The central idea — automatic context, structured engineering reasoning, and controlled AI review — works today for schematic-level questions in KiCad, while the platform architecture is defined to grow beyond any single editor.

---

## Related documents

| Topic | Document |
|-------|----------|
| Platform architecture | [Platform Architecture](../Architecture/Platform_Architecture.md) |
| KiCad host implementation | [Software Architecture (KiCad Host)](../Architecture/KiCad_AI_Integration_Software_Architecture.md) |
| Host integration contract | [ADP-009](../Architecture/ADP-009-Host-Integration-Layer.md) |
| Implementation backlog | [Master Task List](../../tasks/MASTER_TASK_LIST.md) |
| First run | [First-Time Setup](../Developer_Handbook/00_First_Time_Setup.md) |
