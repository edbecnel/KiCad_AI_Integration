[Home](../../../../README.md) · [Project Index](../../../../PROJECT_INDEX.md) · [Engineering Knowledge](../../README.md) · [Circuit Families](../README.md) · [Blocking Oscillator](README.md) · Stage 05

> **AERF stage:** 5 — Operating Modes · **Authoritative stage defs:** [AERF Stage Index](../../AERF_Stage_Index.md)

---
title: Operating Modes
level: 5
circuit_family: Blocking Oscillator
status: Draft
---

# 05 - Operating Modes

**Previous:** [[04 - Component Roles]] · **Next:** [[06 - System Behavior]] · **Knowledge Base:** [[README]]

---

# Purpose

Identify distinct operating states and transitions for the blocking oscillator.

# Canonical modes

1. **Startup / bias establishment** — initial conditions until regenerative feedback exceeds threshold
2. **Transistor on (magnetizing)** — primary current ramps; flux increases; trigger reinforces conduction
3. **Turn-off transition** — base drive collapses; transistor exits saturation; voltage stresses rise
4. **Flyback / reset** — energy transfers to secondary; core flux resets toward balance
5. **Idle / insufficient bias** — oscillation ceases if supply or bias is inadequate

# Mode boundaries

Mode transitions depend on core saturation, transistor storage time, winding phasing, and load. Mis-phased trigger windings prevent sustained oscillation. Heavy secondary loading can shorten flyback interval and alter frequency.

# Simulation hooks

SPICE transient analysis can validate mode timing when SUBCKT models and winding polarity are correct. Simulation validates prior reasoning; it does not replace staged identification (ADR-0007 / ADP-008).

# Output schema hook

Maps to AERF stage 5 `determinations`: mode list, entry/exit conditions, and dominant mode under nominal bias.
