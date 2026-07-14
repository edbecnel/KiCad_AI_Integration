# Roadmap

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Architecture](README.md) › Roadmap

> **Status:** Draft
> **Owner:** Project maintainers
> **Applies To:** KiCad AI Integration release phases
> **Authoritative:** No

## Purpose

High-level phase roadmap for KiCad AI Integration. Detailed implementation tasks live in [Master Task List](../../tasks/MASTER_TASK_LIST.md).

## Phase 1 — Python Script MVP

Stateless one-shot AI requests from inside KiCad. See [ADR-0003](ADRs/ADR-0003-Stateless-Phase-1-Context-Model.md).

Components:

- Context Collection Engine
- Project Context Model
- Prompt Builder
- AI Provider Layer — Claude Sonnet 3.5
- wxPython dialog UI

Exit criteria: Engineer runs one script in KiCad, approves context transmission, receives a context-aware Claude response without manual export.

## Phase 2 — Native KiCad Plugin

Evolve to installable plugin with persistent multi-turn chat.

Features:

- Dockable AI window
- Conversation Manager with session history
- Markdown rendering, template library
- Token usage and cost estimation
- Multi-provider profile switching

## Phase 3 — Advanced Engineering Assistant

Domain-specific audit workflows beyond free-form chat:

- One-click schematic and PCB review
- Power integrity, signal integrity, EMI/EMC guidance
- Component comparison and datasheet analysis
- KiCad Python script and SPICE simulation generation

## Related Documents

- [Software Architecture](KiCad_AI_Integration_Software_Architecture.md)
- [Master Task List](../../tasks/MASTER_TASK_LIST.md)
- [Project Charter](../../PROJECT_CHARTER.md)

## Parent

- [Architecture](README.md)
