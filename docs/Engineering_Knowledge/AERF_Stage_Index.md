# AERF Stage Index

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Engineering Knowledge](README.md) › AERF Stage Index

> **Authoritative specification:** [ADP-008: AI Engineering Reasoning Framework](../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md)

> **Reasoning methodology:** [Engineering Reasoning Methodology](Engineering_Reasoning_Methodology.md) defines *how* each stage performs engineering reasoning. This document defines *what* each stage must determine.

This document is the human-readable index of canonical AERF reasoning stages. Circuit families may override stage titles for stages 1–6; `stage_id` and dependency order are fixed.

### Blocking Oscillator KB (reference family)

Stage-aligned KB files for the first complete circuit family ([`blocking_oscillator`](Circuit_Families/Blocking_Oscillator/README.md)):

| Stage | KB document |
|-------|-------------|
| 0 | [00 - Circuit Identification](Circuit_Families/Blocking_Oscillator/00 - Circuit Identification.md) |
| 1 | [01 - Basic Oscillation](Circuit_Families/Blocking_Oscillator/01 - Basic Oscillation.md) |
| 2 | [02 - Energy Flow](Circuit_Families/Blocking_Oscillator/02 - Energy Flow.md) |
| 3 | [03 - Physical Principles](Circuit_Families/Blocking_Oscillator/03 - Physical Principles.md) |
| 4 | [04 - Component Roles](Circuit_Families/Blocking_Oscillator/04 - Component Roles.md) |
| 5 | [05 - Operating Modes](Circuit_Families/Blocking_Oscillator/05 - Operating Modes.md) |
| 6 | [06 - System Behavior](Circuit_Families/Blocking_Oscillator/06 - System Behavior.md) |
| 7 | [07 - Engineering Analysis](Circuit_Families/Blocking_Oscillator/07 - Engineering Analysis.md) |

---

## Stage 0 — Circuit Identification

| Field | Value |
|-------|-------|
| `stage_id` | 0 |
| `stage_key` | `circuit_identification` |
| `title` | Circuit Identification |
| `question` | What is this circuit? |

### Required determinations

- Circuit family
- Topology
- Functional blocks
- Inputs
- Outputs
- Switching method (if applicable)
- Energy storage method (if applicable)

### Output schema (`determinations`)

```json
{
  "family_id": "string",
  "family_label": "string",
  "topology": "string",
  "functional_blocks": [{"name": "string", "description": "string"}],
  "inputs": [{"name": "string", "type": "string", "description": "string"}],
  "outputs": [{"name": "string", "type": "string", "description": "string"}],
  "switching_method": "string|null",
  "energy_storage_method": "string|null"
}
```

---

## Stage 1 — Basic Operation

| Field | Value |
|-------|-------|
| `stage_id` | 1 |
| `stage_key` | `basic_operation` |
| `title` | Basic Operation (overridable per family) |
| `question` | How does it work? |

### Required determinations

- Operating sequence
- Startup behavior
- Switching mechanism
- Oscillation cycle (if applicable)
- Control mechanism

### Output schema (`determinations`)

```json
{
  "operating_sequence": ["string"],
  "startup_behavior": "string",
  "switching_mechanism": "string|null",
  "oscillation_cycle": "string|null",
  "control_mechanism": "string"
}
```

---

## Stage 2 — Energy Flow

| Field | Value |
|-------|-------|
| `stage_id` | 2 |
| `stage_key` | `energy_flow` |
| `title` | Energy Flow (overridable per family, e.g. Signal Flow) |
| `question` | Where does the energy go? |

### Required determinations

- Energy source
- Storage elements
- Transfer path
- Losses
- Outputs

### Output schema (`determinations`)

```json
{
  "energy_source": "string",
  "storage_elements": [{"element": "string", "role": "string"}],
  "transfer_path": "string",
  "losses": [{"mechanism": "string", "location": "string", "estimate": "string|null"}],
  "outputs": [{"name": "string", "form": "string", "description": "string"}]
}
```

---

## Stage 3 — Physical Principles

| Field | Value |
|-------|-------|
| `stage_id` | 3 |
| `stage_key` | `physical_principles` |
| `title` | Physical Principles |
| `question` | Why does it behave this way? |

### Required determinations

- Magnetic behavior
- Electric field interactions
- Semiconductor physics
- Governing equations

### Output schema (`determinations`)

```json
{
  "magnetic_behavior": "string|null",
  "electric_field_interactions": "string|null",
  "semiconductor_physics": "string|null",
  "governing_equations": [{"name": "string", "expression": "string", "applicability": "string"}]
}
```

---

## Stage 4 — Component Roles

| Field | Value |
|-------|-------|
| `stage_id` | 4 |
| `stage_key` | `component_roles` |
| `title` | Component Roles |
| `question` | What does every component contribute? |

### Required determinations

Per component: functional purpose, interactions, design intent, possible substitutions

### Output schema (`determinations`)

```json
{
  "components": [
    {
      "reference": "string",
      "value": "string",
      "purpose": "string",
      "interactions": ["string"],
      "design_intent": "string",
      "possible_substitutions": [{"part": "string", "tradeoffs": "string"}]
    }
  ]
}
```

---

## Stage 5 — Operating Modes

| Field | Value |
|-------|-------|
| `stage_id` | 5 |
| `stage_key` | `operating_modes` |
| `title` | Operating Modes |
| `question` | How does behavior change? |

### Required determinations

Behavior under: startup, steady state, fault conditions, loading changes, component failures, environmental changes

### Output schema (`determinations`)

```json
{
  "modes": [
    {
      "mode": "startup|steady_state|fault|loading_change|component_failure|environmental",
      "description": "string",
      "behavior": "string",
      "risks": ["string"]
    }
  ]
}
```

---

## Stage 6 — System Behavior

| Field | Value |
|-------|-------|
| `stage_id` | 6 |
| `stage_key` | `system_behavior` |
| `title` | System Behavior |
| `question` | How does the complete system behave? |

### Required determinations

- Mechanical interactions
- Thermal effects
- Environmental influences
- External systems

### Output schema (`determinations`)

```json
{
  "mechanical_interactions": "string|null",
  "thermal_effects": "string|null",
  "environmental_influences": "string|null",
  "external_systems": [{"system": "string", "interaction": "string"}]
}
```

---

## Stage 7 — Engineering Analysis

| Field | Value |
|-------|-------|
| `stage_id` | 7 |
| `stage_key` | `engineering_analysis` |
| `title` | Engineering Analysis |
| `question` | What conclusions can an experienced engineer draw? |

### Required determinations

- Performance evaluation
- Failure analysis
- Optimization suggestions
- Simulation interpretation
- Measurement recommendations
- Design improvements
- Conclusions

### Output schema (`determinations`)

```json
{
  "performance_evaluation": "string",
  "failure_analysis": [{"failure_mode": "string", "cause": "string", "mitigation": "string"}],
  "optimization_suggestions": [{"area": "string", "suggestion": "string", "tradeoffs": "string"}],
  "simulation_interpretation": "string|null",
  "measurement_recommendations": [{"measurement": "string", "instrument": "string", "expected_result": "string"}],
  "design_improvements": [{"improvement": "string", "rationale": "string"}],
  "conclusions": ["string"]
}
```

---

## Per-stage envelope (all stages)

Every stage output includes this envelope in addition to `determinations`:

```json
{
  "stage_id": 0,
  "stage_key": "circuit_identification",
  "title": "Circuit Identification",
  "question": "What is this circuit?",
  "determinations": {},
  "open_questions": [],
  "confidence": "high|medium|low",
  "unknowns": [],
  "simulation_hooks": [
    {
      "description": "string",
      "validates": "string",
      "expected_outcome": "string"
    }
  ],
  "sources": ["project_context", "circuit_family_kb", "prior_stages", "ekm"]
}
```

Significant determinations should carry knowledge classification and evidence chains per [Engineering Reasoning Methodology](Engineering_Reasoning_Methodology.md). Prompt and write-back contract: [ADP-007](../Architecture/ADP-007-AERF-Prompt-Integration.md).

---

## Related Documents

- [ADP-008: AERF Foundation](../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md)
- [Engineering Reasoning Methodology](Engineering_Reasoning_Methodology.md)
- [Circuit Families](Circuit_Families/README.md)
- [Engineering Knowledge](README.md)

## Parent

- [Engineering Knowledge](README.md)
