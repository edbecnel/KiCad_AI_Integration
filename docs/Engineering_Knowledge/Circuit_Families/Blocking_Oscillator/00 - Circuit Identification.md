---
title: Circuit Identification
level: 0
category: Oscillator Analysis
circuit_family: Blocking Oscillator
status: Draft
tags:
  - electronics
  - oscillator
  - blocking-oscillator
  - flyback
  - bedini
  - kicad-ai
  - engineering
  - knowledge-base
---
# 00 - Circuit Identification

**Previous:** None

**Next:** [[01 - Basic Oscillation]]

**Knowledge Base:** [[README]]

---

# Purpose

Before an engineer can analyze how a circuit operates, they must first identify **what kind of circuit it is**.

This document establishes the engineering identity of the Bedini SSG Radiant Oscillator and serves as the foundation for all subsequent analysis.

Circuit identification is the process of recognizing:

- Circuit family
- Intended purpose
- Functional blocks
- Energy source
- Energy destination
- Control method
- Switching topology
- Major operating principles

Only after these have been identified can deeper engineering analysis begin.

---

# Engineering Classification

The Bedini SSG can be classified in several ways depending upon the level of abstraction.

## Primary Classification

**Self-Oscillating Blocking Oscillator**

This is the most fundamental description of the circuit. It repeatedly switches current through an inductor using regenerative magnetic feedback.

---

## Secondary Classification

**Magnetically Coupled Flyback Converter**

The circuit stores energy in a magnetic field and releases that energy as a high-voltage flyback pulse.

---

## Switching Method

**Regenerative Magnetic Feedback**

Unlike RC oscillators, switching is controlled by magnetic coupling between two windings.

---

## Energy Storage Method

**Inductive Energy Storage**

Energy is temporarily stored in the magnetic field surrounding the primary winding.

---

## Primary Switching Device

**NPN Bipolar Junction Transistor (BJT)**

The transistor alternates between cutoff and saturation to repeatedly store and release energy.

---

# Primary Purpose

The purpose of the Bedini SSG is to interrupt current flowing through an inductive winding, generating high-voltage flyback pulses that are directed into a secondary battery.

The circuit simultaneously performs several functions:

- Generates self-sustaining oscillation.
- Stores energy in an inductor.
- Produces inductive flyback pulses.
- Transfers recovered energy into a charging battery.

---

# System Inputs

## Electrical

- Primary battery

## Magnetic

- Trigger winding feedback

## Mechanical (Complete Bedini SSG)

- Permanent magnets attached to the rotor

---

# System Outputs

## Electrical

- High-voltage flyback pulse

## Energy Storage

- Charging battery

## Mechanical

- Rotor torque

## Thermal

- Heat generated in the transistor, wiring, and coil resistance

## Electromagnetic

- Radiated electromagnetic fields

---

# Functional Blocks

The circuit can be divided into several functional blocks.

## Power Source

Provides electrical energy to the oscillator.

Components:

- Primary Battery

---

## Switching Stage

Controls current through the primary winding.

Components:

- Q1

---

## Energy Storage

Stores energy within a magnetic field.

Components:

- Primary winding of T1

---

## Magnetic Feedback

Provides regenerative base drive to the transistor.

Components:

- Trigger winding of T1

---

## Bias Network

Provides initial transistor conduction during startup.

Components:

- Base resistors

---

## Flyback Rectifier

Directs inductive collapse energy toward the charging battery.

Components:

- D1

---

## Energy Storage Destination

Receives recovered flyback energy.

Components:

- Charging Battery

---

# Energy Conversion Chain

The overall energy conversion process is:

```text
Chemical Energy
        │
        ▼
Electrical Energy
        │
        ▼
Magnetic Field
        │
        ▼
Flyback Pulse
        │
        ▼
Electrical Energy
        │
        ▼
Chemical Energy
```

---

# Circuit Topology

The circuit contains three primary paths.

## Power Path

```text
Primary Battery
        │
        ▼
Primary Winding
        │
        ▼
Switching Transistor
        │
        ▼
Ground
```

---

## Feedback Path

```text
Primary Winding
        │
Magnetic Coupling
        │
        ▼
Trigger Winding
        │
        ▼
Base Network
        │
        ▼
Transistor Base
```

---

## Flyback Path

```text
Primary Winding
        │
Inductive Collapse
        │
        ▼
Flyback Diode
        │
        ▼
Charging Battery
```

---

# Distinguishing Characteristics

The Bedini SSG differs from many common oscillators because:

- No capacitor is required for timing.
- Oscillation is controlled by magnetic feedback.
- Energy is stored in an inductor rather than a capacitor.
- Switching is self-sustaining once oscillation begins.
- Output energy is delivered as high-voltage flyback pulses.

---

# Engineering Keywords

The following concepts describe this circuit:

- Blocking Oscillator
- Self-Oscillating Converter
- Flyback Converter
- Pulse Charger
- Regenerative Feedback
- Positive Feedback
- Inductive Energy Storage
- Magnetic Coupling
- Flyback Pulse
- Inductive Collapse

---

# AI Recognition Goals

A KiCad AI assistant should recognize the following without user intervention whenever possible:

- Circuit family
- Oscillator type
- Switching topology
- Energy storage element
- Feedback mechanism
- Switching device
- Functional blocks
- Power flow
- Flyback path
- Charging path

These identifications form the semantic foundation for all subsequent engineering reasoning.

---

# Summary

Circuit identification is the first step in engineering analysis.

Before explaining how the circuit operates, an engineer first recognizes what type of circuit it is, how energy moves through it, and what function each major subsystem performs.

This identification process establishes the context required for deeper understanding of oscillation, magnetic behavior, component interaction, operating modes, and engineering optimization.

---

## Continue Reading

Next document:

➡️ [[01 - Basic Oscillation]]