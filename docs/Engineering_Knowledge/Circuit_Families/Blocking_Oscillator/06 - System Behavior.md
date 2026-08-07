---
title: System Behavior
level: 6
circuit_family: Blocking Oscillator
status: Draft
---

# 06 - System Behavior

[Home](../../../../README.md) · [Project Index](../../../../PROJECT_INDEX.md) · [Engineering Knowledge](../../README.md) · [Circuit Families](../README.md) · [Blocking Oscillator](README.md)

**Previous:** [[05 - Operating Modes]] · **Next:** [[07 - Engineering Analysis]] · **Knowledge Base:** [[README]]

---

# Purpose

Describe how the circuit behaves as a complete system when interacting with supply, load, and control boundaries.

# System-level observations

- **Oscillation frequency** emerges from magnetizing inductance, core properties, bias, and load — often not set by a separate RC timing network
- **Output pulsation:** secondary delivers bursts aligned with flyback events, not continuous DC (unless filtered externally)
- **Load sensitivity:** secondary loading affects reset time and may quench oscillation at extreme conditions
- **Supply sensitivity:** input voltage changes alter current slope and peak flux, shifting frequency and amplitude
- **Thermal drift:** transistor gain and core losses shift operating point over time

# Integration context

In Bedini SSG variants, additional charge/recovery networks may appear on the secondary. System behavior analysis must treat those networks as part of the **load boundary**, not as isolated subcircuits.

# Measurement recommendations

Capture simultaneous waveforms: primary current or proxy, collector/drain voltage, secondary voltage, and supply current. Compare against mode model from stage 5.

# Output schema hook

Maps to AERF stage 6 `determinations`: frequency/period estimates, waveform character, load/supply sensitivity, stability concerns.
