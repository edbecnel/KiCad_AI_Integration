# Engineering Reasoning Methodology

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Engineering Knowledge](README.md) › Engineering Reasoning Methodology

> **Authoritative architecture:** [ADP-008: AI Engineering Reasoning Framework](../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md) (v1.1)

This document defines the **engineering reasoning methodology** common to every AERF stage. It describes *how* each stage performs engineering reasoning. It is not a software architecture document and does not replace ADP-008 or the [AERF Stage Index](AERF_Stage_Index.md).

---

## 1. Purpose and Scope

The [AI Engineering Reasoning Framework (AERF)](../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md) defines **when** reasoning occurs — the canonical sequence of eight stages (0–7) between context collection and EKM population.

The [AERF Stage Index](AERF_Stage_Index.md) defines **what** each stage must determine — required determinations, output schemas, and stage-specific engineering questions.

This document defines **how** every stage performs engineering reasoning — the internal methodology that produces explainable, traceable conclusions regardless of circuit family or engineering discipline.

The same reasoning engine applies to conventional analog circuits, digital systems, switching power supplies, RF circuits, embedded systems, research prototypes, and experimental energy systems. Only the engineering knowledge, evidence classifications, and confidence assessments differ.

---

## 2. Relationship to AERF

```text
AERF (ADP-008)
    Defines WHEN reasoning occurs.

↓

Stage Definitions (AERF Stage Index)
    Define WHAT each stage must determine.

↓

Engineering Reasoning Methodology (this document)
    Defines HOW each stage performs engineering reasoning.
```

Every AERF stage executes using this common methodology. The stage defines the engineering questions; this document defines the reasoning process used to answer them.

---

## 3. Reasoning Process

Regardless of circuit family or engineering discipline, each stage follows a consistent reasoning process:

1. **Evidence collection** — gather all available inputs for the current stage (`ProjectContext`, Circuit Family KB, prior stage outputs, EKM sections, user hints)
2. **Observation classification** — classify each significant input according to the [knowledge classification model](#4-knowledge-classification-model)
3. **Hypothesis generation** — form one or more engineering hypotheses that explain the observations
4. **Competing hypotheses** — evaluate alternative explanations where evidence permits; prefer the hypothesis best supported by evidence
5. **Topology recognition** — identify circuit topology and structural patterns relevant to the stage
6. **Component role inference** — determine what each component contributes within the current analysis scope
7. **Energy and signal path tracing** — trace energy transfer and signal flow where applicable to the stage
8. **Physical principle inference** — ground behavior in applicable physical principles and governing equations
9. **Confidence estimation** — assess overall confidence for stage conclusions (`high`, `medium`, `low`)
10. **Unknown identification** — explicitly flag information that cannot currently be determined
11. **Contradictory evidence handling** — surface conflicts between observations, inferences, or frameworks without suppressing them
12. **Traceable conclusion generation** — produce determinations linked to evidence chains

Stages emphasize different steps (for example, Stage 0 emphasizes topology recognition; Stage 3 emphasizes physical principle inference), but all stages follow this methodology.

---

## 4. Knowledge Classification Model

Every significant engineering statement produced during AERF reasoning shall be assigned a knowledge classification. The AI shall never represent assumptions, hypotheses, theoretical frameworks, project design intent, or engineering interpretations as established engineering knowledge.

This classification model applies to **engineering statements produced during AERF reasoning**. It does not rename extracted KiCad data in `ProjectContext`, which remains correctly described as extracted facts in [ADP-008 §7](../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md#7-authority-boundaries).

### Measured Observation

Directly observed or measured data.

Examples: oscilloscope waveforms, battery voltage measurements, current measurements, frequency measurements, temperature measurements.

These are empirical observations.

**Classification key:** `measured_observation`

### Derived Inference

Conclusions produced through engineering reasoning.

Every derived inference should include supporting evidence, a reasoning chain, and a confidence assessment.

**Classification key:** `derived_inference`

### Mainstream Engineering Model

Engineering models widely accepted and routinely applied in current engineering practice.

Examples: Ohm's Law, Kirchhoff's Laws, conventional semiconductor models, standard transformer theory, accepted battery chemistry models.

These serve as the default engineering framework unless the project specifies otherwise.

**Classification key:** `mainstream_engineering_model`

### Theoretical Framework

The theoretical basis under which the project is being analyzed.

Examples: conventional electromagnetic theory, alternative electromagnetic formulations, project-specific theoretical models.

The AI should record the framework being used without attempting to determine whether it is ultimately correct. Reasoning should remain internally consistent within the selected framework while clearly identifying when it differs from mainstream engineering practice.

**Classification key:** `theoretical_framework`

### Project Design Intent

Statements supplied by the circuit designer describing the intended operation of the system.

Examples: "This circuit captures radiant energy." / "The collapse spike charges the secondary battery." / "The bifilar winding intentionally modifies magnetic behavior."

These describe design intent. They should be preserved as part of the engineering context rather than automatically accepted or rejected.

**Classification key:** `project_design_intent`

### Engineering Assumption

Temporary assumptions introduced during analysis because complete information is unavailable.

Assumptions should remain explicitly identified and revisited as additional evidence becomes available.

**Classification key:** `engineering_assumption`

### Engineering Hypothesis

A proposed explanation that has not yet been confirmed.

Hypotheses remain visible throughout the reasoning process and may later be strengthened, weakened, or rejected based on evidence.

**Classification key:** `engineering_hypothesis`

### Simulation Result

Results generated through simulation.

Simulation validates or challenges hypotheses but remains dependent upon the assumptions and mathematical models used by the simulator. Simulation results should remain distinct from physical measurements.

**Classification key:** `simulation_result`

### Open Question

Items requiring additional engineering investigation or experimentation.

**Classification key:** `open_question`

### Unknown

Information that cannot currently be determined.

Unknowns should remain explicit. The AI shall never fabricate information simply to eliminate unknowns.

**Classification key:** `unknown`

---

## 5. Evidence Chains

Every significant engineering determination should be traceable through an evidence chain:

```text
ProjectContext
        ↓
Observed Evidence
        ↓
Knowledge Classification
        ↓
Engineering Reasoning
        ↓
Derived Inference
        ↓
Confidence Assessment
```

Evidence chains produce explainable engineering reasoning rather than opaque AI conclusions. They allow engineers to inspect why every conclusion was reached.

### Example evidence chain

```json
{
  "statement": "L1 stores energy during the switch-on phase",
  "classification": "derived_inference",
  "confidence": "medium",
  "evidence": [
    {
      "classification": "measured_observation",
      "source": "project_context",
      "detail": "L1 in series with switching node SW1"
    },
    {
      "classification": "mainstream_engineering_model",
      "source": "circuit_family_kb",
      "detail": "Inductor energy storage: E = ½LI²"
    }
  ],
  "reasoning": "Topology places L1 in the energy-transfer path; conventional buck/boost analysis applies.",
  "contradictions": [],
  "unknowns": ["Core saturation behavior at peak current not verified"]
}
```

Formal JSON schema requirements for evidence chains in stage output envelopes are defined in [ADP-007](../Architecture/ADP-007-AERF-Prompt-Integration.md) (prompt integration). This document defines the conceptual model.

---

## 6. Scientific Neutrality Principle

AERF remains scientifically neutral. Its purpose is **not** to determine which scientific theory is ultimately correct.

Its purpose is to:

- reason transparently,
- distinguish observation from interpretation,
- respect the stated design intent,
- classify every conclusion,
- preserve the provenance of engineering knowledge.

Scientific neutrality does **not** mean abandoning accepted engineering principles. It means avoiding premature dismissal of project-specific theories while maintaining complete transparency about their evidentiary status.

The AI should not reject unconventional research projects simply because their theoretical basis differs from mainstream engineering practice. Likewise, it should not elevate those theories to established engineering fact.

Two engineers may interpret identical measurements using different theoretical frameworks. The AI should preserve that distinction. Its responsibility is not to arbitrate scientific debates but to preserve observations, classify knowledge, reason transparently, identify assumptions, expose confidence levels, and explain how conclusions were reached.

---

## 7. Respect for Design Intent

**Respect the circuit designer's stated intent.**

The reasoning process should distinguish between:

- what has been measured,
- what has been observed,
- what has been inferred,
- what has been hypothesized,
- what is accepted engineering practice,
- what theoretical framework the project adopts,
- what remains unknown.

This enables the AI to analyze unconventional research projects fairly while maintaining engineering rigor.

Project design intent (classification: `project_design_intent`) is preserved as engineering context. It informs hypothesis generation and framework selection but is not automatically treated as confirmed engineering knowledge.

---

## 8. Integrity Principle

Rather than relying solely on the narrow rule "the AI must not invent facts," AERF adopts this broader principle:

> **The AI shall never represent assumptions, hypotheses, theoretical frameworks, project design intent, or engineering interpretations as established engineering knowledge.**

Instead, every significant statement shall be explicitly classified according to its evidentiary status using the [knowledge classification model](#4-knowledge-classification-model).

The objective is not to determine which scientific framework is ultimately correct. The objective is to preserve scientific integrity by clearly distinguishing:

- empirical observations,
- derived inferences,
- accepted engineering models,
- theoretical frameworks,
- project design intent,
- engineering assumptions,
- engineering hypotheses,
- simulation results,
- unknowns,
- and open questions.

When `unknowns` cannot be resolved from available evidence, they remain explicit in stage output. The AI must not fabricate information to fill gaps.

---

## 9. Contradictory Evidence

When observations, inferences, assumptions, or frameworks conflict:

1. **Surface the contradiction** — do not suppress or silently resolve conflicting evidence
2. **Classify each side** — identify the knowledge classification of each conflicting statement
3. **Assess impact** — determine whether the contradiction affects stage determinations or overall confidence
4. **Lower confidence when warranted** — contradictions that cannot be resolved should reduce confidence and may produce `open_questions`
5. **Preserve both views** — when frameworks differ, record the mainstream interpretation and the project-framework interpretation separately

Contradictions between `project_design_intent` and `mainstream_engineering_model` are common in research-oriented circuits. These should be documented, not used as grounds for dismissing the project.

---

## 10. Human Review Points

The following conditions should trigger explicit human review flags in stage output (`open_questions`, lowered `confidence`, or entries in `unknowns`):

- Overall stage confidence is `low`
- Contradictory evidence cannot be resolved from available inputs
- Knowledge classification is ambiguous for a significant determination
- A determination depends heavily on `engineering_assumption` without supporting evidence
- The selected `theoretical_framework` differs from `mainstream_engineering_model` for a critical determination
- Simulation would be required to distinguish competing hypotheses

Human approval gates for cloud transmission and EKM write-back are defined in [ADP-008 §9](../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md#9-stage-execution-model).

---

## 11. Relationship to EKM Provenance

AERF knowledge classifications are **reasoning-time** labels applied to engineering statements during stage analysis. They describe the evidentiary status of conclusions as they are produced.

[ADP-001 §13](../Architecture/ADP-001-Engineering-Knowledge-Model-Foundation.md#13-future-metadata) defines **persistence-time** provenance metadata for curated EKM items (source, confidence, status, timestamp, revision history). That metadata is deferred to ADP-005.

| Layer | When applied | Purpose |
|-------|--------------|---------|
| AERF knowledge classification | During stage reasoning | Classify evidentiary status of engineering statements |
| EKM provenance metadata | After user approval, at persistence | Track source, status, and history of curated knowledge |

Terminology should align between layers, but they serve different roles. AERF stage artifacts are transient reasoning outputs; the EKM stores curated conclusions distilled from those artifacts.

---

## Related Documents

- [ADP-008: AI Engineering Reasoning Framework](../Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md)
- [AERF Stage Index](AERF_Stage_Index.md)
- [ADR-0007: AERF Foundation](../Architecture/ADRs/ADR-0007-AERF-Foundation.md)
- [ADP-001: EKM Foundation](../Architecture/ADP-001-Engineering-Knowledge-Model-Foundation.md)
- [Engineering Knowledge](README.md)

## Parent

- [Engineering Knowledge](README.md)
