# KiCad AI Integration — Software Architecture

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Architecture](README.md) › Software Architecture

> **Status:** Draft
> **Owner:** Project maintainers
> **Applies To:** KiCad AI Integration architecture
> **Authoritative:** No

## Overview

KiCad AI Integration is an engineering assistant that operates directly inside KiCad.

Its purpose is to collect engineering context from the active project, construct optimized prompts, communicate with external AI models, and present engineering guidance without requiring engineers to manually export project information.

The initial implementation targets Claude Sonnet 3.5 using the Anthropic API.

Future versions should support multiple AI providers through a common interface.

---

# Project Goals

- Minimize manual copy/paste operations.
- Automatically gather engineering context.
- Provide intelligent design reviews.
- Assist with schematic development.
- Assist with PCB layout.
- Explain existing circuits.
- Detect common engineering mistakes.
- Recommend improvements.
- Generate KiCad Python scripts.
- Maintain conversational context.

---

# Phase 1

Python script executed from within KiCad.

Responsibilities:

- Read current schematic
- Read PCB
- Read project metadata
- Read netlist
- Gather ERC results
- Gather DRC results
- Gather BOM
- Package context
- Build structured prompt
- Call Claude API
- Display response

No persistent chat.

---

# Phase 2

Standalone KiCad Plugin

Features

- Dockable AI window
- Conversation history
- Multiple prompt templates
- Project-aware context
- Incremental context updates
- Token usage statistics
- Cost estimates

---

# Phase 3

Advanced Engineering Assistant

Capabilities

- Interactive engineering discussions
- Automatic design review
- PCB layout review
- Power integrity review
- Signal integrity guidance
- EMC suggestions
- Design-rule interpretation
- Datasheet analysis
- Component comparison
- Generate KiCad scripts
- Generate SPICE simulations
- Suggest alternative circuits
- Staged circuit analysis via [AERF](ADP-008-AI-Engineering-Reasoning-Framework.md) (proposed; not implemented)

---

# Major Software Components

## 1. Context Collection Engine

Responsible for gathering information from KiCad.

Inputs

- .kicad_sch
- .kicad_pcb
- project file
- netlists
- BOM
- ERC
- DRC

Optional inputs (user opt-in)

- schematic image — high-resolution PNG rasterized at 600 DPI via `kicad-cli sch export pdf` + `pdftoppm` (see [ADR-0004](ADRs/ADR-0004-Optional-Multimodal-Schematic-Context.md))

Outputs

Structured project model including optional `schematic_image` bytes and metadata (dpi, sheet, byte size).

Optional artifact paths: shared library (`artifact_library_path`) and per-project `kicad_ai/project_manifest.json` — see [Netlist Gap Fill](../Specifications/Netlist_Gap_Fill.md).

---

## 2. Project Context Model

Internal representation of the current design.

Should contain

- components
- footprints
- nets
- hierarchy
- board statistics
- constraints
- selected objects
- user preferences
- schematic_image (optional) — PNG bytes and metadata when multimodal context is enabled

---

## 2a. AERF Orchestrator (proposed, not implemented)

Staged engineering reasoning pipeline between context collection and prompt conclusions. See [ADP-008](ADP-008-AI-Engineering-Reasoning-Framework.md).

Responsibilities (planned)

- Circuit family recognition
- Load Circuit Family KB excerpts from `docs/Engineering_Knowledge/`
- Execute AERF stages 0–7 sequentially with accumulated context
- Emit structured JSON per stage
- Route simulation hooks to simulation subsystem (future ADP-006)
- Distill approved conclusions to EKM (future ADP-007)

Target location: `src/reasoning/` (not yet created)

---

## 3. Prompt Builder

Converts project context into optimized prompts.

Responsibilities

- token optimization
- summarization
- chunking
- prompt templates
- conversation memory

---

## 4. AI Provider Layer

Abstract interface.

Initial implementation

Claude Sonnet 3.5

Future providers

- Claude
- OpenAI
- Gemini
- Groq
- Ollama
- DeepSeek

---

## 5. Conversation Manager

Maintains

- chat history
- project history
- prompt history
- engineering decisions

---

## 6. KiCad User Interface

Initially

Python dialog.

Eventually

Dockable chat window.

Future

- syntax highlighting
- code blocks
- markdown rendering
- image rendering
- clickable component references

---

# Security

- Never hardcode API keys.
- Store credentials securely.
- Allow multiple provider profiles.
- Support offline local models.
- Never transmit projects automatically.
- Require explicit user approval before cloud uploads.

---

# Long-Term Vision

Transform KiCad into an AI-assisted engineering environment where the AI understands the active design, remembers prior discussions, and acts as an engineering partner rather than a generic chatbot.

## Parent

- [Architecture](README.md)

## Related Documents

- [ADP-008: AI Engineering Reasoning Framework](ADP-008-AI-Engineering-Reasoning-Framework.md)
- [Project Index](../../PROJECT_INDEX.md)
- [Master Task List](../../tasks/MASTER_TASK_LIST.md)
- [Developer Handbook](../Developer_Handbook/README.md)
- [ADR-0004: Optional Multimodal Schematic Context](ADRs/ADR-0004-Optional-Multimodal-Schematic-Context.md)