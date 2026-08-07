# Prompt Architecture

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Architecture](README.md) › Prompt Architecture

> **Status:** Maintained
> **Owner:** Project maintainers
> **Applies To:** KiCad AI Integration prompt construction
> **Last Reviewed:** 2026-08-07
> **Review Frequency:** Quarterly
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
- Netlist gap-fill — connectivity inference and SUBCKT `.lib` generation (see [Netlist Gap Fill](../Specifications/Netlist_Gap_Fill.md))

## Structured Prompt Sections

Prompts use structured XML-style sections:

- `<functional_description>` — user design intent and constraints
- `<kicad_python_extracted_data>` — PCB/schematic extraction JSON
- `<kicad_netlist>` — connectivity data when relevant
- `<kicad_netlist_gap_fill>` — connectivity inference and/or SUBCKT `.lib` generation output when gap-fill is invoked
- `<pico_firmware>` — optional external firmware for cross-review

See [Prompting Guide](../AI/Prompting_Guide.md) and [Programmatic AI Analysis Guide](../Developer_Handbook/Guide-Programmatic_AI_Analysis.md).

## Multimodal Context

Optional high-resolution schematic images supplement text context for spatial and topology audits. See [ADR-0004](ADRs/ADR-0004-Optional-Multimodal-Schematic-Context.md).

### When to include a schematic image

- Netlist-vs-visual cross-reference audits
- Flyback loop, isolation barrier, and high-voltage path topology questions
- Component label OCR when dense schematics make text extraction ambiguous

Do **not** include by default — text extraction and netlists suffice for many connectivity questions. Images increase token cost significantly.

### Export pipeline

```text
kicad-cli sch export pdf --black-and-white → pdftoppm -png -r 600 → PNG bytes
```

Default rasterization DPI is **600**. Project experience validated that 300 DPI is insufficient for readable component labels on dense schematics.

### Dependencies

- `kicad-cli` (bundled with KiCad 8+)
- Poppler `pdftoppm` for PDF → PNG rasterization

### User approval

Schematic images require explicit user opt-in via the "Include schematic image" checkbox and Approve & Send step before cloud transmission.

## Netlist Gap-Fill Prompt Templates

When symbols lack complete netlist data or simulation models, the Prompt Builder may invoke gap-fill templates. See [Netlist Gap Fill](../Specifications/Netlist_Gap_Fill.md) for the full specification.

### Connectivity inference

Expected output in `<kicad_netlist_gap_fill>`:

- Structured JSON listing inferred pin-to-net assignments per reference designator
- Confidence notes per inference
- Explicit flags for ambiguous or unverifiable connections

### SUBCKT / `.lib` generation

**Step 1 — Resolve datasheet** (see [Netlist Gap Fill](../Specifications/Netlist_Gap_Fill.md)):

1. Shared artifact library (`catalog.json`, dedupe by `sha256`)
2. Per-project `kicad_ai/project_manifest.json` (links + schematic/component refs)
3. Symbol `Datasheet` field → import or link into shared library
4. User attach via UI → shared library + update `referenced_by`
5. Global `datasheet_search_paths`
6. Controlled `https:` fetch → cache to shared library

Do **not** prompt user to search the web.

**Step 2 — Route by evidence:**

| Tier | When | Action |
|------|------|--------|
| **A — Datasheet-backed** | PDF resolved | Two-stage: extract facts from PDF → synthesize `.SUBCKT` → validate |
| **B — Context synthesis** | No PDF; KiCad pins, fields, footprint, schematic context | Multi-source prompt; pin order from **KiCad symbol**; label `context_synthesized` |
| **C — Last resort** | Thin context only | Inferred behavioral model; `needs-manual-review`; label `inferred_last_resort` |

Part-number-only one-liners (e.g. `Can you create an ngspice-friendly SUBCKT .lib file for this part: F0D3180?`) are **not** used by the built-in Prompt Builder.

Tier B prompt must include symbol pin list, value, footprint, fields, and optional schematic image — not part number alone.

Expected SUBCKT deliverables: `generated.lib`, KiCad hookup notes, `validation.json`, `provenance.json`, tier label.

Gap-fill and SUBCKT output is **advisory only** — engineers must verify against ERC, the schematic, and datasheets before applying changes.

## AERF Stage Prompt Templates

**Implemented** in `src/prompts/templates/aerf_stage.py` and `build_aerf_stage_prompt()` in `src/prompts/builder.py`. Architecture defined in [ADP-008](ADP-008-AI-Engineering-Reasoning-Framework.md).

Per-stage prompt templates for the eight AERF reasoning stages (0–7). Each stage prompt includes:

- `<aerf_stage>` — current stage metadata (id, key, title, question)
- `<aerf_prior_stages>` — accumulated JSON from prior stages
- `<circuit_family_kb>` — excerpts from the loaded circuit family knowledge base
- `<kicad_python_extracted_data>` — `ProjectContext` JSON
- `<engineering_knowledge>` — relevant EKM sections when present
- `<aerf_methodology>` — knowledge classification and evidence-chain guidance from [Engineering Reasoning Methodology](../Engineering_Knowledge/Engineering_Reasoning_Methodology.md)

Dry-run assembly: `build_aerf_stage_prompt()` / `build_aerf_stage_prompt_bundle()` in EIE — no auto cloud send. Full multi-stage orchestration with approval gating is deferred.

Stage templates follow the same XML-section conventions as other prompts. The SUBCKT two-stage pipeline (`facts` → `synthesis`) is a precedent for staged orchestration but is not itself an AERF stage.

See [AERF Stage Index](../Engineering_Knowledge/AERF_Stage_Index.md), [Engineering Reasoning Methodology](../Engineering_Knowledge/Engineering_Reasoning_Methodology.md), and [Engineering Knowledge](../Engineering_Knowledge/README.md).

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
- [ADR-0004: Optional Multimodal Schematic Context](ADRs/ADR-0004-Optional-Multimodal-Schematic-Context.md)
- [ADP-008: AI Engineering Reasoning Framework](ADP-008-AI-Engineering-Reasoning-Framework.md)
- [Netlist Gap Fill](../Specifications/Netlist_Gap_Fill.md)
- [Master Task List](../../tasks/MASTER_TASK_LIST.md) § 1.3

## Parent

- [Architecture](README.md)
