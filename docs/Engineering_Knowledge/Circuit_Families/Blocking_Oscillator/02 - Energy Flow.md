[Home](../../../../README.md) · [Project Index](../../../../PROJECT_INDEX.md) · [Engineering Knowledge](../../README.md) · [Circuit Families](../README.md) · [Blocking Oscillator](README.md) · Stage 02

> **AERF stage:** 2 — Energy Flow · **Authoritative stage defs:** [AERF Stage Index](../../AERF_Stage_Index.md)

---
title: Energy Flow
level: 2
circuit_family: Blocking Oscillator
status: Draft
---

# 02 - Energy Flow

**Previous:** [[01 - Basic Oscillation]] · **Next:** [[03 - Physical Principles]] · **Knowledge Base:** [[README]]

---

# Purpose

Trace how energy enters, stores, transfers, and exits the blocking oscillator during one switching cycle.

# Required determinations (blocking oscillator)

- **Primary energy source:** DC supply on the primary winding path
- **Energy storage:** Magnetic field in the flyback/transformer core during transistor on-time
- **Energy transfer:** Collapse of magnetic field couples energy to secondary and trigger windings when the transistor turns off
- **Loss paths:** Conduction loss in the switching transistor, core hysteresis, winding resistance, clamp/snubber networks (if present)
- **Output delivery:** Secondary winding delivers pulses to load and/or recovery networks depending on topology variant

# Engineering notes (Bedini SSG family)

During the on-phase, energy accumulates in the core rather than being delivered continuously to the load. The blocking oscillator topology intentionally interrupts primary current to force a flyback event. Analysis of “radiant” or recovery claims must separate **measured electrical power** at the supply from **observed secondary behavior** without overstating unverified energy gain.

# Output schema hook

Maps to AERF stage 2 `determinations`: energy sources, storage elements, transfer paths, and dominant loss mechanisms.
