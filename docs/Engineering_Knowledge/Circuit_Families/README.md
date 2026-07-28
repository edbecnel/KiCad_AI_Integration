# Circuit Families

[Home](../../../README.md) › [Project Index](../../../PROJECT_INDEX.md) › [Engineering Knowledge](../README.md) › Circuit Families

> **Authoritative specification:** [ADP-008 §10–12](../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md)

Circuit families provide reusable domain knowledge organized by AERF reasoning stage. Each family shares the same stage IDs (0–7) and dependency order while allowing stage title overlays and family-specific determinations.

---

## Registry

Planned circuit families (content not yet authored):

| `family_id` | Directory | Status |
|-------------|-----------|--------|
| `blocking_oscillator` | `Blocking_Oscillator/` | Planned — first reference KB (next milestone) |
| `flyback` | `Flyback/` | Planned |
| `buck` | `Buck/` | Planned |
| `boost` | `Boost/` | Planned |
| `linear_regulator` | `Linear_Regulator/` | Planned |
| `operational_amplifier` | `Operational_Amplifier/` | Planned |
| `audio_amplifier` | `Audio_Amplifier/` | Planned |
| `digital_logic` | `Digital_Logic/` | Planned |

---

## Per-family directory structure

```text
Circuit_Families/
└── <Family_Name>/
    ├── README.md                      # Family overview, recognition signatures
    ├── 00_Circuit_Identification.md
    ├── 01_<FamilySpecificStageTitle>.md
    ├── 02_<FamilySpecificStageTitle>.md
    ├── ...
    └── 07_Engineering_Analysis.md
```

### File naming rules

- **Prefix:** Two-digit `stage_id` (`00` through `07`)
- **Suffix:** Underscore-separated title matching the family's stage overlay or the default AERF title
- **README.md:** Required at family root — overview, recognition signatures, related families

### Example: Blocking Oscillator

```text
Blocking_Oscillator/
├── README.md
├── 00_Circuit_Identification.md
├── 01_Basic_Oscillation.md
├── 02_Energy_Flow.md
├── 03_Physical_Principles.md
├── 04_Component_Roles.md
├── 05_Operating_Modes.md
├── 06_System_Behavior.md
└── 07_Engineering_Analysis.md
```

### Example: Operational Amplifier (title overlays)

```text
Operational_Amplifier/
├── README.md
├── 00_Circuit_Identification.md
├── 01_Basic_Operation.md
├── 02_Signal_Flow.md          # overlay: "Signal Flow" instead of "Energy Flow"
├── 03_Physical_Principles.md
├── ...
└── 07_Engineering_Analysis.md
```

---

## Stage title overlay rules

| stage_id | Overlay allowed? | Notes |
|----------|------------------|-------|
| 0 | No | `Circuit Identification` is fixed |
| 1–6 | Yes | Family-appropriate titles (e.g. Basic Oscillation, Signal Flow, Timing Analysis) |
| 7 | No | `Engineering Analysis` is fixed |

Stage IDs and execution order are **never** overridden.

---

## Recognition signatures

Each family `README.md` should document recognition signatures used by the circuit family classifier (implementation deferred):

- Typical component patterns (switching devices, transformers, op-amps, logic gates)
- Net naming conventions
- Topology heuristics
- Distinguishing features from related families

Example recognition basis for flyback vs buck: presence of galvanic isolation, transformer with separate primary/secondary windings, output rectifier on secondary.

---

## KB content guidelines

Each stage file should include:

1. **Purpose** — what this stage determines for this family
2. **Key concepts** — domain-specific terminology and principles
3. **Typical determinations** — what an experienced engineer would identify
4. **Common unknowns** — what often requires measurement or user input
5. **Simulation hooks** — typical simulations that validate this stage for this family
6. **Related families** — cross-references for similar topologies

KB content is reference material for prompt injection — not per-project instance data.

---

## Adding a new circuit family

1. Create directory under `Circuit_Families/<Family_Name>/`
2. Add `README.md` with overview and recognition signatures
3. Create stage files `00` through `07` following naming rules
4. Register the family in this README's registry table
5. No plugin code changes required (per [ADP-008 §17](../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md))

---

## Related Documents

- [AERF Stage Index](../AERF_Stage_Index.md)
- [ADP-008: AERF Foundation](../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md)
- [Engineering Knowledge](../README.md)

## Parent

- [Engineering Knowledge](../README.md)
