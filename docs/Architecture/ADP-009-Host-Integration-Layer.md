# ADP-009: Host Integration Layer

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Architecture](README.md) › ADP-009

**Status:** Accepted (v1.0)

**Author:** Ed Becnel

**Project:** KiCad AI Integration (first host reference implementation)

**Version:** 1.0

**Date:** 2026-07-29

**Ratified by:** [ADR-0009](ADRs/ADR-0009-Platform-Architecture-Foundation.md)

**Builds on:** [Platform Architecture](Platform_Architecture.md), [ADP-001](ADP-001-Engineering-Knowledge-Model-Foundation.md) (v1.1)

---

## 1. Purpose

This Architectural Design Proposal defines the **Host Integration Layer** — the contract between the AI-assisted Electrical Engineering Reasoning Platform and any host engineering environment (EDA tool, standalone application, web service, CLI, or laboratory system).

KiCad AI Integration is the **first reference implementation** of this layer. This document does not require relocating existing KiCad-specific code or documentation.

---

## 2. Problem Statement

Platform frameworks (EKM, AERF, EIE, prompts, providers) must remain independent of KiCad file formats, APIs, and UI toolkits. Without an explicit host boundary, platform logic drifts into KiCad-specific parsers and dialogs, blocking future integrations.

---

## 3. Goals

The Host Integration Layer shall:

- Define a `DesignSnapshot` contract for extracted design facts
- Specify host responsibilities: collect, link, present UI, manage artifact roots, optional write-back
- Document KiCad as the reference implementation without generalizing prematurely
- Preserve existing `ProjectContext` as the KiCad `DesignSnapshot` implementation
- Defer `HostLink` generalization beyond `KiCadLink` until a second host requires it

---

## 4. Non-Goals

This ADP does NOT:

- Require immediate physical reorganization of `src/` into `src/hosts/`
- Replace [ADR-0001](ADRs/ADR-0001-KiCad-8-Minimum-Version.md) (KiCad host capability contract)
- Redefine EKM, AERF, or authority boundaries in ADP-001
- Mandate a specific UI framework for all hosts

---

## 5. DesignSnapshot Contract

A `DesignSnapshot` is an ephemeral, refreshable representation of **what the design is** — extracted facts, not engineering interpretation.

### Required capabilities

| Capability | Description |
|------------|-------------|
| `project_path` | Host project root or equivalent identifier |
| `project_name` | Human-readable project label |
| `to_dict()` / `to_json()` | Serializable representation for prompts and logging |

### Optional fields (host-dependent)

Hosts may populate additional fields. The KiCad reference implementation (`ProjectContext`) includes symbols, datasheet resolutions, connectivity, PCB summary, netlist summary, and optional schematic image bytes.

### Protocol location

[`src/platform_core/contracts.py`](../../src/platform_core/contracts.py) defines the `DesignSnapshot` protocol. [`src/context/model.py`](../../src/context/model.py) `ProjectContext` is the KiCad implementation.

---

## 6. Host Responsibilities

| Responsibility | Description |
|----------------|-------------|
| **Context collection** | Read host design files and tools; produce a `DesignSnapshot` |
| **UI shell** (optional) | Present platform outputs; enforce approve-before-send for cloud transmission |
| **Artifact root** | Per-project directory for manifests, exports, generated assets (KiCad: `kicad_ai/`) |
| **Object linking** | Structured references from EKM to host objects (KiCad: `KiCadLink` in EKM schema) |
| **Write-back** (optional) | Apply approved changes to host design files (KiCad: schematic field mutation) |

Everything above the Host Integration Layer — EIE, EKM, AERF, prompts, providers — is shared platform code.

---

## 7. KiCad Reference Implementation

| Host responsibility | KiCad implementation |
|--------------------|---------------------|
| Context collection | `src/context/collector.py`, `schematic_*.py`, `pcb_summary.py`, `netlist_export.py` |
| CLI tools | `src/utils/kicad_cli.py` |
| UI shell | `src/ui/` (wxPython, optional `pcbnew`) |
| Artifact root | `<project>/kicad_ai/` |
| Object linking | `KiCadLink` in [`docs/Database/ekm_schema_v1.json`](../Database/ekm_schema_v1.json) |
| Write-back | `schematic_write.py`, `schematic_sim_write.py` |
| Native plugin (planned) | `src/plugin/` |
| Entry points | `scripts/run_ai_assistant.py`, `src/ui/launcher.py` |

---

## 8. Future Hosts

A new host implements the same five responsibilities with host-specific collectors and link types. Platform frameworks require no changes.

`HostLink` generalization (a union type or polymorphic link replacing KiCad-only `KiCadLink`) is deferred to a future ADP when a second host is actively developed.

---

## 9. Acceptance Criteria

- `DesignSnapshot` protocol is defined in code
- `ProjectContext` satisfies the protocol without rename
- Platform modules do not import KiCad parsers or UI
- KiCad host behavior is documented in [KiCad Software Architecture](KiCad_AI_Integration_Software_Architecture.md)

---

## Related Documents

- [Platform Architecture](Platform_Architecture.md)
- [ADP-010: Engineering Inference Engine](ADP-010-Engineering-Inference-Engine.md)
- [ADR-0009: Platform Architecture Foundation](ADRs/ADR-0009-Platform-Architecture-Foundation.md)
- [KiCad Software Architecture](KiCad_AI_Integration_Software_Architecture.md)

## Parent

- [Architecture](README.md)
