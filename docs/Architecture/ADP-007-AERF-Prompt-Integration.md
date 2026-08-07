# ADP-007: AERF Prompt Integration and EKM Write-Back

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Architecture](README.md) › ADP-007

**Status:** Accepted (v1.0 — retrospective; implementation complete)

**Author:** Ed Becnel

**Project:** KiCad AI Integration

**Version:** 1.0

**Date:** 2026-08-07

**Builds on:** [ADP-002: EKM Schema and Persistence](ADP-002-EKM-Schema-and-Persistence.md) (v1.0), [ADP-008: AI Engineering Reasoning Framework](ADP-008-AI-Engineering-Reasoning-Framework.md) (v1.1), [ADP-010: Engineering Inference Engine](ADP-010-Engineering-Inference-Engine.md) (v1.0)

**Related ADRs:** [ADR-0007: AERF Foundation](ADRs/ADR-0007-AERF-Foundation.md)

---

## 1. Purpose

This Architectural Design Proposal defines **AERF prompt integration** — per-stage prompt templates, EKM context assembly at prompt time, and the **stage-output → EKM write-back mapping** for approved AERF conclusions.

Implementation shipped in Track C (`src/prompts/templates/aerf_stage.py`, `src/ekm/aerf_writeback.py`). This document retroactively records the contract for EDF traceability.

---

## 2. Problem Statement

AERF requires eight sequential LLM calls with accumulated context, circuit-family KB excerpts, optional EKM sections, and structured XML-style prompt sections per [Prompt Architecture](Prompt_Architecture.md).

Approved stage outputs must map to stable EKM sections without ad-hoc field naming. Without a documented mapping, write-back logic drifts from [ADP-008 §15](ADP-008-AI-Engineering-Reasoning-Framework.md#15-relationship-to-ekm) and notebook presentation breaks.

---

## 3. Goals

ADP-007 shall:

- Define per-stage AERF prompt template sections (`<aerf_stage>`, `<aerf_prior_stages>`, `<circuit_family_kb>`, etc.)
- Specify EKM excerpt inclusion rules at prompt time
- Document the canonical AERF stage → EKM section write-back mapping
- Gate cloud transmission and EKM persistence behind user approval (Approve & Send, `--approve-ekm-writeback`)
- Support staleness-aware prompt assembly (detection contract from ADP-002; full UI indicators deferred)

---

## 4. Non-Goals

- AERF stage definitions (see ADP-008 and [AERF Stage Index](../Engineering_Knowledge/AERF_Stage_Index.md))
- Simulation closed loop ([ADP-006](ADP-006-Simulation-Abstraction.md))
- Natural-language → EKM capture (ADP-004, not authored)
- Provenance metadata on write-back fields (ADP-005, not authored)

---

## 5. Per-Stage Prompt Template

Implemented in [`src/prompts/templates/aerf_stage.py`](../../src/prompts/templates/aerf_stage.py).

### XML sections

| Section | Content |
|---------|---------|
| `<aerf_stage>` | `stage_id`, `stage_key`, `title`, stage question |
| `<aerf_prior_stages>` | JSON envelopes from stages 0 through N−1 |
| `<circuit_family_kb>` | Excerpt from `docs/Engineering_Knowledge/Circuit_Families/` |
| `<kicad_python_extracted_data>` | Compact `DesignSnapshot` JSON |
| `<engineering_knowledge>` | Relevant EKM sections when present |
| `<user_question>` | Optional user focus for the stage |

### System prompt

Requests structured JSON: `stage_id`, `stage_key`, `determinations`, `open_questions`, `unknowns`, `confidence`. Significant determinations include knowledge classification and evidence chains per [Engineering Reasoning Methodology](../Engineering_Knowledge/Engineering_Reasoning_Methodology.md).

### Builder API

`build_aerf_stage_sections(snapshot, family_id, stage_id, prior_stages=..., ekm_sections=...)` returns section name → body for the Prompt Builder.

---

## 6. EKM Write-Back Mapping

Implemented in [`src/ekm/aerf_writeback.py`](../../src/ekm/aerf_writeback.py) (`write_aerf_stages_to_ekm`, dry-run plan via `plan_aerf_writeback`).

| AERF output | EKM destination |
|-------------|-----------------|
| Stage 0 determinations (family, topology, I/O) | Section: Circuit Overview |
| Stage 1–3 determinations | Section: Operation and Principles |
| Stage 4 determinations | Section: Component Rationale |
| Stage 5–6 determinations | Section: Operating Conditions |
| Stage 7 conclusions | Sections: Analysis, Recommendations, Open Items |
| `open_questions` | Open Items fields with status `Pending Review` |

Write-back requires separate user approval from stage cloud transmission (`--approve-ekm-writeback`, AERF UI **Write to EKM**).

---

## 7. Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Per-stage prompt template | Implemented | `src/prompts/templates/aerf_stage.py` |
| Prompt assembly in AERF pipeline | Implemented | `src/inference/aerf.py` |
| EKM write-back mapping | Implemented | `src/ekm/aerf_writeback.py` |
| CLI dry-run / apply | Implemented | `--aerf-plan`, `--approve-ekm-writeback` |
| AERF UI write-back | Implemented | `src/ui/aerf_dialog.py` |
| Staleness flags in prompts | Partial (detection contract only; UI indicators deferred) |
| EKM summarization / token budgeting | Partial (compact snapshot helper; full summarization deferred) |

---

## 8. Acceptance Criteria

- [x] Per-stage AERF prompt template exists with documented XML sections
- [x] `build_aerf_stage_sections()` assembles stage, prior stages, KB, snapshot, and optional EKM
- [x] Stage-output → EKM section mapping implemented and documented
- [x] Write-back gated behind explicit user approval
- [x] Dry-run plan available before persistence (`plan_aerf_writeback`)
- [ ] Staleness indicators at prompt time when links are stale (partial — contract only)
- [ ] Full EKM summarization for large notebooks at prompt time (deferred)

---

## Related Documents

- [ADP-008: AI Engineering Reasoning Framework](ADP-008-AI-Engineering-Reasoning-Framework.md)
- [ADP-010: Engineering Inference Engine](ADP-010-Engineering-Inference-Engine.md)
- [Prompt Architecture](Prompt_Architecture.md)
- [AERF Stage Index](../Engineering_Knowledge/AERF_Stage_Index.md)
- [Master Task List](../../tasks/MASTER_TASK_LIST.md)

## Parent

- [Architecture](README.md)
