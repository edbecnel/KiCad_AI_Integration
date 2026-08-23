# AERF Validation Rubric
[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [User Guides](README.md) › AERF Validation Rubric


[Home](../../README.md) · [Project Index](../../PROJECT_INDEX.md) · [User Guides](README.md) · AERF Validation Rubric

> **Status:** Maintained
> **Owner:** Project maintainers
> **Applies To:** Live AERF validation on reference circuits (Bedini SSG Radiant Oscillator)
> **Last Reviewed:** 2026-08-22
> **Review Frequency:** When circuit-family KB or AERF prompts change

Use this checklist during a **live** AERF run (real API, `--approve-send` or **Approve & Send** in `--ui-aerf`). Automated mock tests validate pipeline mechanics; this rubric validates **engineering quality** of stage JSON.

For how staged analysis works, see [How AERF Works](How_AERF_Works.md). For step-by-step UI instructions, see [Testing With Your KiCad Project](Testing_With_Your_KiCad_Project.md).

---

## Reference project

| Item | Value |
|------|-------|
| Project | `Bedini_SSG_Radiant_Oscillator.kicad_pro` |
| Circuit family | `blocking_oscillator` |
| Stages | 0–7 (eight LLM calls) |

---

## Per-stage pass criteria (Bedini / blocking oscillator)

| Stage | Question (summary) | Pass criteria |
|-------|-------------------|---------------|
| **0** | What is this circuit? | Identifies blocking oscillator / Bedini SSG; names trifilar coil, switching transistor, flyback path; `family_id` is `blocking_oscillator` |
| **1** | How does it work? | Plausible on/off sequence and regenerative magnetic feedback; startup behavior not fabricated |
| **2** | Where does the energy go? | Energy path: primary store → flyback → secondary/recovery; separates supply power from secondary observations |
| **3** | Why does it behave this way? | Physical principles stated with appropriate confidence; equations optional, not nonsense |
| **4** | What does every component contribute? | Major refs (Q, coil windings, diodes, batteries) mapped to roles |
| **5** | How does behavior change? | Modes (e.g. saturated vs cutoff) distinguished |
| **6** | How does the complete system behave? | System-level behavior includes load/recovery boundary; mechanical/thermal marked unknown if N/A |
| **7** | What conclusions can an engineer draw? | Conclusions, measurements, and open questions actionable; **radiant** claims classified (hypothesis vs measured) per KB neutrality |

---

## Red flags (fail / retry stage)

- Wrong topology (e.g. RC oscillator, push-pull) or wrong `family_id`
- Hallucinated parts or nets not present in schematic context
- Missing required `determinations` keys for the stage (see `src/reasoning/stage_schemas.py`)
- `confidence: high` with empty evidence or no `unknowns` where context is incomplete
- Parse or validation errors from `validate_stage_envelope()`
- Presenting hypotheses or design intent as established facts without `knowledge_classification`

---

## Live validation workflow

1. **Pre-flight** — `pytest tests/integration/test_bedini_aerf_exit.py`; dry-run `--aerf-pipeline` (no `--approve-send`).
2. **Live run** — `--ui-aerf` (recommended) or CLI `--aerf-pipeline --approve-send --aerf-family blocking_oscillator`.
3. **Review** — Check each stage JSON against the table above.
4. **EKM** — **Write to EKM…** after Stage 7 passes; verify in Notebook and `ekm_tool validate`.
5. **Sign-off** — Record date and reviewer in [Master Task List](../../tasks/MASTER_TASK_LIST.md) §AERF.

### UI launch

```bash
python scripts/run_ai_assistant.py \
  "/path/to/Bedini_SSG_Radiant_Oscillator.kicad_pro" \
  --ui-aerf
```

Enable **Include schematic image** for large schematics. Use **Build preview** before each **Approve & Send**.

### CLI launch

```bash
python scripts/run_ai_assistant.py "$BEDINI_PRO" \
  --aerf-pipeline --approve-send --aerf-family blocking_oscillator
```

---

## EKM sections expected after write-back

After successful write-back, expect EKM sections mapped from stages (see `src/ekm/aerf_writeback.py`):

- `circuit_overview`
- `operation_and_principles`
- `component_rationale`
- `operating_conditions`
- `analysis`
- `recommendations`
- `open_items`

Validate:

```bash
python scripts/ekm_tool.py validate "$(dirname "$BEDINI_PRO")"
python scripts/ekm_tool.py show "$(dirname "$BEDINI_PRO")"
```

---

## Related documents

- [How AERF Works](How_AERF_Works.md)
- [Testing With Your KiCad Project](Testing_With_Your_KiCad_Project.md)
- [E2E Full Flow](../Developer_Handbook/07_E2E_Full_Flow.md)
- [AERF Stage Index](../Engineering_Knowledge/AERF_Stage_Index.md)
- [Blocking Oscillator KB](../Engineering_Knowledge/Circuit_Families/Blocking_Oscillator/README.md)

## Parent

- [User Guides](README.md)