# Engineering Knowledge

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › Engineering Knowledge

> **Documentation path:** [Project Index](../../PROJECT_INDEX.md) → Engineering Knowledge

## Purpose

This EDF domain contains the **AI Engineering Reasoning Framework (AERF)** reference knowledge and circuit-family documentation that supports staged engineering analysis.

Engineering Knowledge is **reference content** — reusable across projects and circuit instances. It is distinct from:

| Store | Role |
|-------|------|
| **Engineering Knowledge** (this domain) | Reusable reasoning stages and circuit-family reference knowledge |
| **EKM** ([ADP-001](../Architecture/ADP-001-Engineering-Knowledge-Model-Foundation.md)) | Per-project curated engineering knowledge (intent, rationale, decisions) |
| **`ProjectContext`** | Extracted KiCad facts from the active design |

## AERF Overview

The [AI Engineering Reasoning Framework (AERF)](../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md) defines eight canonical reasoning stages (0–7) that the AI follows before producing engineering conclusions.

Rather than sending a schematic directly to an LLM, the plugin progressively builds engineering understanding through staged reasoning. Simulation validates prior understanding; it does not substitute for it.

**Ratified by:** [ADR-0007](../Architecture/ADRs/ADR-0007-AERF-Foundation.md)

## Domain Contents

| Document | Purpose |
|----------|---------|
| [AERF_Stage_Index.md](AERF_Stage_Index.md) | Canonical stage definitions, determinations, and output schemas |
| [Circuit_Families/README.md](Circuit_Families/README.md) | Circuit family registry, naming conventions, overlay rules |

## AI Workflow (Conceptual)

```text
Parse Schematic → ProjectContext
       ↓
Recognize Circuit Family
       ↓
Load Circuit Family KB
       ↓
Reason through Stages 0–7
       ↓
Generate Questions / Simulation Hooks
       ↓
Interpret Results (future)
       ↓
Generate Engineering Conclusions → EKM (after user approval)
```

## What Belongs Here

- AERF stage definitions and output schemas
- Circuit-family reference knowledge organized by stage
- Recognition signatures and family overviews
- Engineering ontology content that generalizes across projects

## What Does Not Belong Here

- Per-project engineering knowledge (belongs in EKM / `kicad_ai/engineering_knowledge.json`)
- KiCad extraction logic (belongs in `src/context/`)
- Prompt template implementation (belongs in `src/prompts/`; architecture in [Prompt Architecture](../Architecture/Prompt_Architecture.md))
- Runtime orchestration code (belongs in `src/reasoning/` when implemented)

## Related Documents

- [ADP-008: AERF Foundation](../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md)
- [ADR-0007: AERF Foundation](../Architecture/ADRs/ADR-0007-AERF-Foundation.md)
- [ADP-001: EKM Foundation](../Architecture/ADP-001-Engineering-Knowledge-Model-Foundation.md)
- [Software Architecture](../Architecture/KiCad_AI_Integration_Software_Architecture.md)
- [Master Task List](../../tasks/MASTER_TASK_LIST.md)

## Parent

- [Project Index](../../PROJECT_INDEX.md)
