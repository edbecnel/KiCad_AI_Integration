# Database

[Home](../../README.md) · [Project Index](../../PROJECT_INDEX.md)

> **Documentation path:** [Project Index](../../PROJECT_INDEX.md) → Database

## Purpose

Data models, schemas, migrations, persistence design, backup, restore, and retention.

## Authoritative Documents

- [ADP-001: Engineering Knowledge Model Foundation](../Architecture/ADP-001-Engineering-Knowledge-Model-Foundation.md) — EKM architecture and minimum metamodel (v1.1)
- [ADP-002: EKM Schema and Persistence](../Architecture/ADP-002-EKM-Schema-and-Persistence.md) — canonical JSON Schema, persistence contract, validation (v1.0)
- [ADR-0005: EKM Foundation](../Architecture/ADRs/ADR-0005-EKM-Foundation.md) — ratified EKM foundation decision
- [ADR-0008: EKM Schema and Persistence](../Architecture/ADRs/ADR-0008-EKM-Schema-and-Persistence.md) — ratified schema and persistence decision

## Schema Artifacts

| File | Version | Description |
|------|---------|-------------|
| [`ekm_schema_v1.json`](ekm_schema_v1.json) | 1.0.0 | Canonical JSON Schema for `kicad_ai/engineering_knowledge.json` |

Migration tooling and CI validation tests are deferred to implementation.

## What Belongs Here

Add documents whose primary responsibility matches this domain.

## Navigation

- [Project Index](../../PROJECT_INDEX.md)
- [Project README](../../README.md)

## Maintenance

Update this index whenever a major document in this domain is created, moved, renamed, or retired.
