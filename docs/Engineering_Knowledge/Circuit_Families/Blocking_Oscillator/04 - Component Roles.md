[Home](../../../../README.md) · [Project Index](../../../../PROJECT_INDEX.md) · [Engineering Knowledge](../../README.md) · [Circuit Families](../README.md) · [Blocking Oscillator](README.md) · Stage 04

> **AERF stage:** 4 — Component Roles · **Authoritative stage defs:** [AERF Stage Index](../../AERF_Stage_Index.md)

---
title: Component Roles
level: 4
circuit_family: Blocking Oscillator
status: Draft
---

# 04 - Component Roles

**Previous:** [[03 - Physical Principles]] · **Next:** [[05 - Operating Modes]] · **Knowledge Base:** [[README]]

---

# Purpose

Assign functional roles to each major component group in a typical blocking oscillator / Bedini SSG schematic.

# Typical roles

| Component group | Role |
|-----------------|------|
| Primary switching transistor | Controls magnetizing current; turns off to initiate flyback |
| Primary winding | Stores energy in core during on-time |
| Trigger (feedback) winding | Provides regenerative base/gate drive while flux rises |
| Secondary winding | Delivers flyback energy to load or charge/recovery network |
| Base/gate bias network | Sets initial bias and limits drive (resistors, diodes) |
| Core (transformer/inductor) | Couples windings; sets magnetizing inductance and coupling |
| Supply decoupling | Stabilizes input during fast current transitions |
| Protection (snubber, TVS, freewheel) | Limits voltage spikes at turn-off |

# KiCad linking

EKM fields may reference symbols via `KiCadLink` (`kind: component`). Extracted `ProjectContext` supplies references and values; roles are engineering interpretation stored in EKM after user approval.

# Output schema hook

Maps to AERF stage 4 `determinations`: per-component or per-block role assignments with confidence.
