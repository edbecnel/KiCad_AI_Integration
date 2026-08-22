# ADP-012: Learning Loop and Canonical Knowledge Engineering

[Home](../../README.md) · [Project Index](../../PROJECT_INDEX.md) · [Architecture](README.md) · ADP-012

**Status:** Accepted (v1.0 — learning loop staging)

**Related:** [ADP-008](ADP-008-AI-Engineering-Reasoning-Framework.md), [ADP-001](ADP-001-Engineering-Knowledge-Model-Foundation.md), [ADP-004](ADP-004-Natural-Language-EKM-Capture.md), [ADP-005](ADP-005-EKM-Provenance.md)

---

## Purpose

Define how KiCad AI Integration **learns while in use**:

1. **Project EKM** — instance knowledge after approved AERF write-back
2. **User artifact library** — staging area for auto-promoted circuit family KB (`~/kicad_ai_library/circuit_families/`)
3. **CKES / ELS** — future Canonical Knowledge Engineering System (export-only contract in Phase L5)

---

## Learning tiers

| Tier | Location | Lifetime | Written by |
|------|----------|----------|------------|
| Repo KB | `docs/Engineering_Knowledge/Circuit_Families/` | Repository | Maintainers |
| User library KB | `<artifact_library>/circuit_families/` | User machine | Auto-promotion (confidence gates) |
| Project EKM | `<project>/kicad_ai/engineering_knowledge.json` | Project | AERF write-back |
| CKES/ELS | External canonical store | Organization | Migration from library |

---

## Auto-promotion gates

Promotion runs after successful EKM write-back when `learning_auto_promote` is true:

- Eight stages parsed and validated
- Each stage confidence meets `learning_min_confidence` (default `high`)
- Consistent `family_id` in Stage 0 (not `generic`)
- Open question count within limit

Implementation: `src/learning/family_promotion.py`

---

## CKES export bundle

`scripts/export_circuit_families.py` produces:

- `families.json`
- Per-family stage markdown + `provenance.json`
- `export_metadata.json` (`export_format: ckes_circuit_families_v1`)

Import into CKES/ELS is out of scope for this repository.

---

## Parent

- [Architecture README](README.md)
