# How AERF Works

[Home](../../README.md) · [Project Index](../../PROJECT_INDEX.md) · [User Guides](README.md) · How AERF Works

> **Status:** Maintained
> **Owner:** Project maintainers
> **Applies To:** KiCad AI Integration — staged circuit analysis
> **Last Reviewed:** 2026-08-07
> **Review Frequency:** Quarterly

This guide explains how the **AI Engineering Reasoning Framework (AERF)** works in practice: what is deterministic, what the LLM does, and how that differs from pasting a netlist into a generic chatbot.

For architecture detail, see [ADP-008](../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md). For stage definitions, see [AERF Stage Index](../Engineering_Knowledge/AERF_Stage_Index.md).

---

## What AERF is (honest summary)

AERF does **not** run a separate non-AI “engineering brain” that fully understands your circuit before any LLM call.

The **LLM is still the inference engine**. AERF wraps it with:

| Layer | What it provides |
|-------|------------------|
| **Process** | Eight engineering stages (0–7) in the order experienced engineers use |
| **Knowledge injection** | Circuit Family KB excerpts per stage |
| **Epistemic discipline** | Knowledge classification, unknowns, confidence, evidence chains |
| **Accumulation** | Prior stage JSON passed into each subsequent prompt |
| **Governance** | Approve & Send per stage; separate approval for EKM write-back |
| **Persistence** | Approved conclusions distilled into the [EKM](../Architecture/ADP-001-Engineering-Knowledge-Model-Foundation.md) |

**Exit criteria** for a good AERF run: reviewable structured JSON per stage and usable EKM after write-back — not proof that the system understood the circuit without AI.

---

## What happens without AI (deterministic)

Before each stage prompt is built, the host collects facts and reference material:

1. **KiCad extraction** — symbols, values, footprints, net labels, hierarchy, netlist summary, datasheet status (`ProjectContext`)
2. **Circuit family classifier** — heuristic match to a registered family (e.g. `blocking_oscillator`) using symbol patterns and net keywords ([`classifier.py`](../../src/reasoning/classifier.py))
3. **User hint or EKM prior** — optional override or reinforcement of family selection
4. **Circuit Family KB load** — stage-specific excerpt from `docs/Engineering_Knowledge/Circuit_Families/`
5. **EKM sections** — authored design intent and prior approved conclusions, if present
6. **Prior stage outputs** — JSON envelopes from stages already completed in this run

None of these steps **infer engineering purpose** for your specific schematic. They supply facts, taxonomy, reference knowledge, and authored intent.

---

## What the LLM does (each AERF stage)

Each stage **0–7** is one LLM call with a scoped question (for example, Stage 0: “What is this circuit?”).

The prompt includes XML sections:

- `<aerf_stage>` — stage metadata and question
- `<aerf_prior_stages>` — accumulated JSON from earlier stages
- `<circuit_family_kb>` — family reference excerpt
- `<kicad_python_extracted_data>` — compact project snapshot
- `<engineering_knowledge>` — EKM excerpts
- `<aerf_methodology>` — reasoning rules (classification, neutrality, integrity)
- `<aerf_evidence_model>` — evidence chain shape
- `<aerf_output_schema>` — required JSON envelope and `determinations` schema

The model returns structured JSON: `determinations`, `confidence`, `unknowns`, `open_questions`, optional `simulation_hooks`. The pipeline validates envelope shape and required `determinations` keys per stage.

---

## Chat vs AERF vs Simulation vs Notebook vs Audits vs Routing

| Surface | Shortcut | CLI | Purpose |
|---------|----------|-----|---------|
| **Chat** | Ctrl+1 | `--ui-chat` | Ad-hoc Q&A — **not** full staged AERF |
| **Datasheets** | Ctrl+2 | `--ui-datasheets` | PDF library and symbol linkage |
| **Simulation** | Ctrl+3 | `--ui-simulation` | SPICE gap scan, SUBCKT generation |
| **AERF** | Ctrl+4 | `--ui-aerf` | Stages 0–7, Approve & Send, EKM write-back |
| **Notebook** | Ctrl+5 | `--ui-notebook` | View/edit EKM after write-back |
| **Audits** | Ctrl+6 | `--audit-schematic` | One-click schematic/PCB/DRC reviews |
| **Routing** | Ctrl+7 | `--ui-routing` | Freerouting autoroute with checkpoint |

Use **AERF** for disciplined multi-stage analysis. Use **Chat** for quick questions. See [05 — AERF](05_AERF_Staged_Analysis.md) for the UI workflow.

---

## Authority boundaries (what each store means)

| Store | Question it answers |
|-------|---------------------|
| KiCad schematic | What is electrically connected? |
| `ProjectContext` | What was extracted from KiCad (facts) |
| Circuit Family KB | What this class of circuit generally is (reference) |
| EKM | What the project team authored or approved (intent, rationale) |
| AERF stage outputs | Transient per-run reasoning (session) |
| LLM inference | Engineering interpretation inside each stage |

The AI must not treat assumptions, design intent, or hypotheses as established facts without `knowledge_classification`.

---

## vs copy-paste into ChatGPT

| Traditional dump | AERF path |
|------------------|-----------|
| Manual export of netlist, PDFs, PNG | Automatic context collection |
| One large prompt | Eight scoped stages with accumulated context |
| Free-form essay answer | JSON with confidence, unknowns, open questions |
| No project memory | EKM persistence after approval |
| No review gate | Approve & Send before cloud transmission |

AERF uses the **same class of LLM** as a browser chatbot. The difference is **workflow, structure, KB injection, governance, and persistence** — not a different intelligence substrate.

---

## Limitations (today)

- Only **Blocking Oscillator** circuit family KB is fully curated in-repo; **generic** scaffold supports unknown topologies
- **Learned** families auto-promote to `~/kicad_ai_library/circuit_families/` when confidence gates pass ([ADP-012](../Architecture/ADP-012-Learning-and-Canonical-Knowledge.md))
- Project EKM auto-loads on subsequent AERF runs on the same project
- Schematic connectivity is partial (net labels; full pin-level graph not yet in context)
- Simulation **closed loop** (run sim → refine stages) is architecture-only ([ADP-006](../Architecture/ADP-006-Simulation-Abstraction.md))
- Chat (`general_review`) does not include full AERF methodology

---

## Related documents

- [AERF Validation Rubric](AERF_Validation_Rubric.md) — live-run quality checklist (Bedini reference)
- [Testing With Your KiCad Project](Testing_With_Your_KiCad_Project.md) — run `--ui-aerf` step by step
- [Feature Overview](Feature_Overview.md) — capability status
- [Engineering Reasoning Methodology](../Engineering_Knowledge/Engineering_Reasoning_Methodology.md)
- [ADP-007](../Architecture/ADP-007-AERF-Prompt-Integration.md) — prompt and write-back contract

## Parent

- [User Guides](README.md)
