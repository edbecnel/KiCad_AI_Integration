# ADP-010: Engineering Inference Engine (EIE)

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Architecture](README.md) › ADP-010

**Status:** Accepted (v1.0)

**Author:** Ed Becnel

**Project:** KiCad AI Integration

**Version:** 1.0

**Date:** 2026-07-29

**Ratified by:** [ADR-0009](ADRs/ADR-0009-Platform-Architecture-Foundation.md)

**Builds on:** [ADP-008](ADP-008-AI-Engineering-Reasoning-Framework.md) (v1.1), [ADP-009](ADP-009-Host-Integration-Layer.md) (v1.0)

---

## 1. Purpose

This Architectural Design Proposal defines the **Engineering Inference Engine (EIE)** — the platform runtime that orchestrates engineering reasoning, prompt construction, and AI provider invocation.

EIE is distinct from **AERF**. AERF defines *what* to reason about (stages, methodology, circuit-family overlays). EIE defines *how* reasoning executes at runtime.

---

## 2. Problem Statement

Today, inference workflows are scattered across `*_supply.py` modules in `src/ui/`, coupling headless orchestration to the KiCad UI package. As EKM and AERF are implemented, a dedicated platform orchestrator is needed that:

- Consumes `DesignSnapshot`, EKM, and Circuit Family KB inputs
- Invokes prompt templates and the AI provider layer
- Executes AERF stages (full or partial)
- Gates cloud transmission and EKM write-back behind user approval
- Remains independent of wxPython and KiCad file I/O

---

## 3. Goals

EIE shall:

- Provide a single platform entry point for inference workflows
- Orchestrate ad-hoc prompts (`general_review`) and future AERF staged analysis
- Delegate stage definitions and KB loading to `src/reasoning/` (AERF)
- Delegate EKM load/save to `src/ekm/`
- Invoke `src/prompts/` and `src/providers/` without KiCad imports
- Support incremental migration from `*_supply.py` modules

---

## 4. Non-Goals

EIE is NOT:

- A replacement for AERF stage definitions (those live in ADP-008 and `docs/Engineering_Knowledge/`)
- A replacement for the EKM schema or Engineering Notebook UI
- A UI framework (host UI shells call into EIE)
- Fully implemented in v1.0 of this ADP (initial chat workflow migration only)

---

## 5. Architecture

```
DesignSnapshot ──┐
EKM (optional) ─┼──► EIE ──► Prompt Builder ──► AI Provider Layer
AERF stages ─────┤         │
Circuit Family KB┘         ├──► Stage artifacts (transient)
                           └──► EKM write-back (user-approved, `write_aerf_stages_to_ekm`)
```

### Component placement

| Component | Package | Role |
|-----------|---------|------|
| EIE orchestrator | `src/inference/` | Workflow coordination, provider invocation |
| AERF stage registry | `src/reasoning/` | Stage definitions, KB excerpt loading |
| EKM runtime | `src/ekm/` | Schema validation, load/save |
| Prompt templates | `src/prompts/` | Prompt assembly |
| AI providers | `src/providers/` | LLM communication |

---

## 6. Workflows

### 6.1 Ad-hoc chat (Phase 1 — implemented)

`src/inference/chat.py` provides:

- `collect_chat_context()` — delegates to host collector
- `build_chat_prompt()` — builds `general_review` prompt
- `send_chat_prompt()` — invokes configured provider

`src/ui/chat_supply.py` re-exports these functions for backward compatibility.

### 6.2 Simulation / SUBCKT gap-fill (partial)

`src/ui/simulation_supply.py` remains host-adjacent until simulation workflow is refactored into `src/inference/simulation.py` (future milestone).

### 6.3 AERF staged analysis (planned)

EIE will:

1. Load circuit family KB excerpts via `src/reasoning/`
2. Execute stages 0–7 sequentially with accumulated context
3. Build per-stage prompts (ADP-007) — implemented in `src/prompts/templates/aerf_stage.py`
4. Execute stages sequentially via `run_aerf_pipeline()` / `run_aerf_stage()` with `approve_send` gate
5. Require user approval per stage or batch before cloud transmission (`--approve-send`, `--ui-aerf`)
6. Route simulation hooks to simulation abstraction (ADP-006, future)
7. Gate EKM write-back (ADP-007, Track C4)

---

## 7. Authority Boundaries

| Data | Owner | EIE role |
|------|-------|----------|
| Extracted facts | `DesignSnapshot` | Read-only input |
| Stage definitions | AERF / `src/reasoning/` | Load and execute |
| Transient stage outputs | EIE session | Emit; do not auto-persist |
| Curated conclusions | EKM | Write only after user approval |
| Raw chat | Conversation Manager | Input; not canonical knowledge |

---

## 8. Implementation Status

| Milestone | Status |
|-----------|--------|
| `src/inference/chat.py` — general review workflow | Implemented |
| `src/inference/simulation.py` — simulation/SUBCKT workflow | Implemented |
| `src/inference/aerf.py` — AERF pipeline + approval-gated send | Implemented |
| `src/ui/aerf_dialog.py` — per-stage AERF UI (Approve & Send) | Implemented |
| `src/reasoning/classifier.py` — heuristic circuit family classifier | Implemented |
| `src/prompts/templates/aerf_stage.py` — per-stage AERF prompts (ADP-007) | Implemented |
| `src/reasoning/` — AERF stage registry + KB loader | Implemented |
| `src/ekm/` — EKM runtime + validation CLI | Implemented |
| EKM write-back from approved AERF stage outputs | Implemented (`src/ekm/aerf_writeback.py`, `write_aerf_stages_to_ekm`) |

---

## 9. Acceptance Criteria

- EIE package exists at `src/inference/` with no KiCad UI imports
- Chat workflow migrated from `chat_supply.py` with backward-compatible re-exports
- AERF and EKM packages exist as documented stubs for future implementation
- Platform import boundaries documented in [Platform Architecture](Platform_Architecture.md)

---

## Related Documents

- [ADP-008: AI Engineering Reasoning Framework](ADP-008-AI-Engineering-Reasoning-Framework.md)
- [ADP-009: Host Integration Layer](ADP-009-Host-Integration-Layer.md)
- [Prompt Architecture](Prompt_Architecture.md)
- [AI Provider Interface](AI_Provider_Interface.md)
- [Platform Architecture](Platform_Architecture.md)

## Parent

- [Architecture](README.md)
