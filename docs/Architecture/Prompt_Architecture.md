# Prompt Architecture

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Architecture](README.md) › Prompt Architecture

> **Status:** Draft
> **Owner:** Project maintainers
> **Applies To:** KiCad AI Integration prompt construction
> **Authoritative:** No

## Purpose

Define how KiCad project context is assembled into optimized prompts for AI providers. This document complements the Prompt Builder component in [Software Architecture](KiCad_AI_Integration_Software_Architecture.md).

## Template System

_To be detailed during Phase 1 implementation._

Planned named engineering audit templates:

- General design review
- PCB layout and trace audit
- Isolation and clearance audit
- Netlist-vs-visual cross-reference

## Structured Prompt Sections

Prompts use structured XML-style sections:

- `<functional_description>` — user design intent and constraints
- `<kicad_python_extracted_data>` — PCB/schematic extraction JSON
- `<kicad_netlist>` — connectivity data when relevant
- `<pico_firmware>` — optional external firmware for cross-review

See [Prompting Guide](../AI/Prompting_Guide.md) and [Programmatic AI Analysis Guide](../Developer_Handbook/Guide-Programmatic_AI_Analysis.md).

## Token Budgeting

_To be detailed during Phase 1 implementation._

Planned strategies:

- Summarize large nets and omit S-expression noise
- Chunk oversized payloads
- Partial context flags — PCB-only, schematic-only, critical-nets-only
- Configurable system-role persona per template

See [Cost Optimization](../AI/Cost_Optimization.md).

## Related Documents

- [Software Architecture](KiCad_AI_Integration_Software_Architecture.md)
- [ADR-0003: Stateless Phase 1 Context Model](ADRs/ADR-0003-Stateless-Phase-1-Context-Model.md)
- [Master Task List](../../tasks/MASTER_TASK_LIST.md) § 1.3

## Parent

- [Architecture](README.md)
