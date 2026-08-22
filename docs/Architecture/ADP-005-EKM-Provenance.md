# ADP-005: EKM Provenance and Confidence

[Home](../../README.md) · [Project Index](../../PROJECT_INDEX.md) · [Architecture](README.md) · ADP-005

**Status:** Stub (partial slice in learning promotion)

**Assigned from:** [ADP-001 Appendix A](ADP-001-Engineering-Knowledge-Model-Foundation.md#appendix-a-deferred-decisions)

---

## Purpose

Define provenance semantics for EKM fields and promoted circuit-family KB: source, confidence, revision history, approval actor.

## Partial implementation

- AERF write-back stores `metadata.source` and `metadata.approved_at` on EKM fields
- Library promotion writes `provenance.json` per learned family ([ADP-012](ADP-012-Learning-and-Canonical-Knowledge.md))

Full provenance UI and revision history remain deferred.

---

## Parent

- [Architecture README](README.md)
