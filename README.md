# KiCad AI Integration

> Bringing AI-assisted circuit design, review, and engineering directly into KiCad.

**New here?** Read [What is the KiCad AI Integration Project?](PROJECT_OVERVIEW.md) for the project's philosophy, evolution, and long-term vision.

**Documentation:** Start at the [Project Index](PROJECT_INDEX.md) for the full documentation map. **Try it:** `python scripts/run_ai_assistant.py --ui` — [Testing With Your KiCad Project](docs/User_Guides/Testing_With_Your_KiCad_Project.md). Acronyms and terminology: [Glossary](docs/Reference/Glossary.md).

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

# Initial Features (Phase 1)

The first release will consist of a Python script that executes within KiCad.

Features include:

- Read the active schematic
- Read the active PCB
- Extract project metadata
- Extract component information
- Extract net information
- Extract BOM data
- Read ERC results
- Read DRC results
- Construct an optimized AI prompt
- Send requests to Claude Sonnet 3.5 via the Anthropic API
- Display AI responses inside KiCad

Initially, conversations will be stateless (one request at a time).

---

# Planned Features

## Phase 2

- Native KiCad plugin
- Dockable AI chat window
- Markdown rendering
- Conversation history
- Multiple prompt templates
- Token usage statistics
- Cost estimation
- Context caching

---

## Phase 3

Advanced engineering capabilities including:

- Automated schematic review
- PCB layout review
- Power integrity analysis
- Signal integrity guidance
- EMI/EMC recommendations
- Design Rule interpretation
- Component comparison
- Datasheet analysis
- Circuit explanation
- Interactive engineering discussions
- Script generation
- Simulation assistance

---

# High-Level Architecture

```
                KiCad
                  │
                  ▼
     Context Collection Engine
                  │
                  ▼
       Project Context Model
                  │
                  ▼
          Prompt Builder
                  │
                  ▼
         AI Provider Interface
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
   Claude      OpenAI      Gemini
      │           │           │
      ▼           ▼           ▼
   Groq       DeepSeek     Ollama
```

This architecture intentionally separates AI providers from the rest of the application to make future expansion straightforward. Platform and host architecture is documented in [`docs/Architecture/`](docs/Architecture/README.md), starting with [Platform Architecture](docs/Architecture/Platform_Architecture.md).

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

**Phase:** Post Track B — platform frameworks complete; **Track C** (AERF + EIE depth) is the recommended next milestone.

**KiCad host (working):** Schematic context, datasheet library and panels (`--ui-datasheets`), chat UI with Approve & Send (`--ui-chat`), simulation/SUBCKT panel (`--ui-simulation`, early), Claude provider, general-review prompts.

**Platform:** EKM runtime + CLI (`src/ekm/`); AERF stage registry + KB loader (`src/reasoning/`); EIE chat, simulation orchestration, and AERF stage-0 stub (`src/inference/`). Blocking Oscillator reference KB complete (stages 00–07).

See [Feature Overview](docs/User_Guides/Feature_Overview.md) for capability status, platform/host separation, and gaps. To validate against your own project, follow [Testing With Your KiCad Project](docs/User_Guides/Testing_With_Your_KiCad_Project.md).

---

# Contributing

Contributions are welcome.

Future contribution guidelines will include:

- Coding standards
- Pull request workflow
- Documentation requirements
- Testing requirements
- Plugin development guidelines

---

# License

License to be determined.

---

# Acknowledgements

This project builds upon the excellent open-source KiCad ecosystem and modern AI technologies to create a next-generation engineering workflow for electronics designers.

Special thanks to the KiCad development community and the AI research community for making this type of integration possible.
