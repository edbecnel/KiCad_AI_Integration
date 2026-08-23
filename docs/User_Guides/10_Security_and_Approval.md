# Security and Approval
[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [User Guides](README.md) › Security and Approval


[Home](../../README.md) · [User Guides](README.md) · Security and Approval

## Overview

KiCad AI Integration uses **explicit approval** before sending project data to an AI provider or writing curated knowledge to disk. This document explains what leaves your machine and where approve gates apply.

## Approve gates

| Feature | Gate | What happens without approval |
|---------|------|------------------------------|
| **Chat** | **Approve & Send** | Nothing sent to provider |
| **AERF** | **Approve & Send stage** (per stage) | Stage not transmitted |
| **AERF** | **Write to EKM…** | No change to `engineering_knowledge.json` |
| **Audits** | Transmission confirmation dialog | Audit not run |
| **Routing** | Run autoroute confirmation | Autoroute not started |
| **Routing** | **Accept candidate** | `.kicad_pcb` not replaced |
| **Datasheets AI** | URL approval dialog (unless auto-fetch enabled) | URL not fetched |

## What may leave your machine (cloud provider)

When using **`ai_provider: claude`** and approving a send, the provider receives:

- Assembled **ProjectContext** (schematic summary, BOM, netlist excerpts, ERC/DRC summaries as enabled)
- Optional **schematic image**
- Optional **firmware file** contents (Chat)
- Optional **PCB selection** context
- **Prompt text** and **conversation history** (Chat)
- **AERF stage prompts** and prior stage outputs (AERF)

Datasheet **AI discovery** sends part metadata and receives suggested URLs — not full PDFs unless you fetch them.

## What stays local

| Data | Location |
|------|----------|
| KiCad project files | Your project directory |
| EKM | `<project>/kicad_ai/engineering_knowledge.json` |
| Datasheet PDFs | `artifact_library_path` (default `~/kicad_ai_library/`) |
| Chat sessions | `<project>/kicad_ai/conversation.json` |
| Audit reports | `<project>/kicad_ai/reviews/` |
| Ollama inference | Your machine when `ai_provider: ollama` |

With **Ollama**, prompts are sent to your local Ollama server — not Anthropic's cloud.

## API keys

- Store in `~/kicad_ai_config.json` or `ANTHROPIC_API_KEY` env var
- Never commit keys to git
- Settings dialog writes config to your home directory

## File write-back

These actions modify files on disk — always confirm dialogs:

- AERF **Write to EKM…**
- Notebook **Save**
- Datasheets **Write URL to schematic** / attach PDF
- Simulation **Apply** / **Apply built-in models**
- Routing **Accept candidate**

## Related documents

- [docs/AI/Security.md](../AI/Security.md) — contributor security notes
- [09 — Configuration Reference](09_Configuration_Reference.md)
- [00 — Getting Started](00_Getting_Started.md)

## Parent

- [User Guides](README.md)