# KiCad AI Integration

> Bringing AI-assisted circuit design, review, and engineering directly into KiCad.

**New here?** Read [What is the KiCad AI Integration Project?](PROJECT_OVERVIEW.md) for the project's philosophy, evolution, and long-term vision.

**Documentation:** Start at the [Project Index](PROJECT_INDEX.md). **User guides:** [docs/User_Guides/README.md](docs/User_Guides/README.md) — install, every tab, workflows. **Quick try:** KiCad **Tools → External Plugins → KiCad AI Assistant** or `python scripts/run_ai_assistant.py --ui`.

## Overview

KiCad AI Integration is an open-source project that integrates modern Large Language Models (LLMs) directly into the KiCad electronic design environment. Rather than a generic AI chat window, it is designed as an **AI-assisted electrical engineering reasoning platform** that builds structured engineering understanding before asking an LLM to reason about a design.

**KiCad is the first host application and reference implementation** — not the architectural boundary of the system. The host-agnostic framework stack is **AERP** (**A**I-assisted **E**ngineering **R**easoning **P**latform): EKM, AERF, EIE, prompts, providers, and related components. See [Platform Architecture](docs/Architecture/Platform_Architecture.md) and [Glossary — AERP](docs/Reference/Glossary.md).

The project automatically collects engineering context from the active KiCad project—including schematics, PCB layouts, netlists, datasheets, and other metadata—and progressively transforms it into structured knowledge through the [Engineering Knowledge Model (EKM)](docs/Architecture/ADP-001-Engineering-Knowledge-Model-Foundation.md) and [AI Engineering Reasoning Framework (AERF)](docs/Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md). See [Project Overview](PROJECT_OVERVIEW.md) for the full story of how the project evolved and where it is headed.

The initial implementation targets **Anthropic Claude**, with a long-term architecture designed to support multiple AI providers through a common abstraction layer.

---

# Project Goals

- Integrate AI directly into KiCad
- Minimize manual copy-and-paste workflows
- Automatically gather engineering context
- Reduce prompt engineering requirements
- Support iterative engineering conversations
- Provide meaningful circuit analysis
- Keep the architecture provider-independent
- Maintain compatibility with future AI models

---

# Current Features

The KiCad AI **Assistant shell** provides seven embedded tabs with shared project context:

| Tab | Shortcut | Purpose |
|-----|----------|---------|
| Chat | Ctrl+1 | Multi-turn schematic-aware Q&A with approve-before-send |
| Datasheets | Ctrl+2 | PDF library, attach, AI discovery |
| Simulation | Ctrl+3 | SUBCKT gap scan and spice write-back |
| AERF | Ctrl+4 | Staged analysis (0–7) with EKM write-back |
| Notebook | Ctrl+5 | Engineering Knowledge editor |
| Audits | Ctrl+6 | One-click schematic/PCB reviews |
| Routing | Ctrl+7 | Freerouting autoroute with checkpoint accept/reject |

**Launch:** KiCad ActionPlugin (**Tools → External Plugins → KiCad AI Assistant**) or `python scripts/run_ai_assistant.py --ui`.

See [User Guides](docs/User_Guides/README.md) for step-by-step instructions.

---

# Initial Features (Phase 1 — historical)

The first release consisted of a Python script that executes within or alongside KiCad:

- Read schematic and PCB from project files
- Construct an optimized AI prompt
- Send requests to Claude via the Anthropic API
- Display responses in wxPython UI

Many Phase 1 goals are now superseded by the unified Assistant shell above.

---

# Planned / in progress

## Product polish

- True wxAUI dock inside PCB editor (Assistant currently uses a non-modal frame)
- Context preview thumbnail for schematic images
- Clickable component references in AI responses

## Advanced engineering

- Simulation closed loop ([ADP-006](docs/Architecture/ADP-006-Simulation-Abstraction.md))
- Deeper PI/SI/EMC guidance beyond current audit templates
- Notebook AI edit proposals

---

# Legacy roadmap notes (superseded items struck through)

## Phase 2 (largely complete)

- ~~Native KiCad plugin~~ — ActionPlugin shipped
- ~~Embedded feature tabs~~ — seven tabs in Assistant shell
- ~~Conversation history~~ — `kicad_ai/conversation.json` per project
- ~~Multiple prompt templates~~ — Chat template selector
- ~~Multi-provider profiles~~ — Claude + Ollama in Settings
- Dockable AI chat window — still deferred (non-modal frame today)

## Phase 3 (partial)

- ~~Automated schematic/PCB review~~ — Audits tab
- ~~Staged AERF with EKM write-back~~ — shipped
- Freerouting routing UI — shipped (Routing tab)
- Power integrity / SI / EMC deep analysis — partial via audits + live context
- Component comparison
- Datasheet analysis
- Circuit explanation
- Interactive engineering discussions
- Script generation
- Simulation assistance

---

# High-Level Architecture

```
KiCad project files
        │
        ▼
Context Collection Engine  ──►  ProjectContext (DesignSnapshot)
        │
        ├──► Heuristic circuit-family classifier + Circuit Family KB
        │
        ▼
Engineering Inference Engine (EIE)
        │
        ├──► AERF staged analysis (stages 0–7, one LLM call per stage)
        ├──► Chat (general_review — ad-hoc Q&A)
        └──► Simulation / SUBCKT workflows
        │
        ▼
Prompt Builder  ──►  AI Provider Layer (Claude, …)
        │
        ▼
User approval  ──►  EKM write-back (curated notebook)
```

Each AERF stage is an **LLM call** with deterministic prep (extract, classify, KB excerpts, prior stage JSON). See [How AERF Works](docs/User_Guides/How_AERF_Works.md).

Platform and host detail: [`docs/Architecture/`](docs/Architecture/README.md), [Platform Architecture](docs/Architecture/Platform_Architecture.md).

---

# Repository Structure

```
KiCad_AI_Integration/
├── README.md
├── PROJECT_OVERVIEW.md           # Project philosophy and vision
├── PROJECT_INDEX.md              # Primary documentation hub
├── PROJECT_CHARTER.md
├── ARCHITECTURE_DECISIONS.md
├── CHANGELOG.md
├── ENGINEERING_DOCUMENTATION_FRAMEWORK.md
│
├── docs/
│   ├── Architecture/             # System design, ADRs
│   ├── AI/                         # AI handbook (Phase 2)
│   ├── Developer_Handbook/         # Setup, environment, integration guides
│   ├── Development/
│   ├── Governance/                 # Phase 2 placeholder
│   ├── Specifications/
│   ├── API/
│   ├── Database/
│   ├── Deployment/
│   ├── User_Guides/
│   ├── Reference/
│   └── Templates/
│
├── tasks/                          # Implementation tracking
├── archive/                        # Retired documentation
│
├── src/
│   ├── context/
│   ├── prompts/
│   ├── providers/
│   ├── platform_core/
│   ├── inference/
│   ├── reasoning/
│   ├── ekm/
│   ├── ui/
│   ├── utils/
│   └── plugin/
│
├── tests/
├── examples/
└── scripts/
```

See [PROJECT_INDEX.md](PROJECT_INDEX.md) for links to all authoritative documents.

---

# Supported AI Providers

Initial support:

- Anthropic Claude Sonnet 3.5

Planned support:

- Anthropic Claude
- OpenAI GPT
- Google Gemini
- Groq
- Ollama
- DeepSeek
- Additional providers through the provider interface

---

# Security

This project takes security seriously.

Guiding principles include:

- API keys are never hardcoded.
- Credentials are stored securely.
- Projects are never transmitted automatically.
- Users explicitly control what information is sent to cloud providers.
- Support for local AI models will be provided whenever practical.

---

# Current Status

**Phase:** Post Track C/D — platform frameworks (Tracks B–D) complete. **Phase 1 close-out** complete (file-based context, gap-fill, housekeeping). **Phase 2** (native plugin, embedded Assistant tabs, multi-turn chat) is the recommended next milestone.

**KiCad host (working):** Launcher (`--ui`), schematic context with pin-level connectivity and gap detection, datasheet library and panels (`--ui-datasheets`), chat UI with Approve & Send and audit templates (`--ui-chat`), simulation/SUBCKT panel (`--ui-simulation`), built-in sim model auto-apply, AERF staged analysis (`--ui-aerf`), Engineering Notebook (`--ui-notebook`), Claude provider, netlist gap-fill template.

**Platform:** EKM runtime + CLI (`src/ekm/`); AERF stage registry, classifier, KB loader, full pipeline, learning loop (`src/reasoning/`, `src/inference/aerf.py`); EIE chat and simulation orchestration (`src/inference/`); EKM write-back from approved AERF stages. Blocking Oscillator reference KB complete (stages 00–07).

See [Feature Overview](docs/User_Guides/Feature_Overview.md) for capability status, platform/host separation, and gaps. To validate against your own project, follow [Testing With Your KiCad Project](docs/User_Guides/Testing_With_Your_KiCad_Project.md).

---

# Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for workflow, testing, and platform import boundaries.

---

# License

MIT License — see [LICENSE](LICENSE).

---

# Acknowledgements

This project builds upon the excellent open-source KiCad ecosystem and modern AI technologies to create a next-generation engineering workflow for electronics designers.

Special thanks to the KiCad development community and the AI research community for making this type of integration possible.
