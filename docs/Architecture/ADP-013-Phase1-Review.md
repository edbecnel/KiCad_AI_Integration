# ADP-013 Phase 1 — Architecture Review

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Architecture](README.md) › Phase 1 Review

> **Status:** Draft — ready for human architecture review
> **Date:** 2026-08-23

## Summary

Phase 1 investigation and architecture for routing abstraction is complete. Phase 2 POC code has been implemented behind the Phase 2 gate checklist. Human architecture review approval remains open.

## Phase 2 Gate Checklist

| Gate | Status | Evidence |
|------|--------|----------|
| ADP-013 routing-engine-neutral | Pass | [ADP-013](ADP-013-Routing-Abstraction.md) — no Freerouting-specific contract fields |
| KiCad DSN export mechanism confirmed | Pass | pcbnew `ExportSpecctraDSN`; **not** `kicad-cli` (KiCad 10.0.4) |
| KiCad SES import mechanism confirmed | Pass | pcbnew `ImportSpecctraSES`; **not** `kicad-cli` |
| Engine-independent RoutingRequest / RoutingEngine | Pass | `src/routing/types.py`, ADP-013 §9 |
| Freerouting as independently installed external tool | Pass | [Freerouting Integration](../Specifications/Freerouting_Integration.md) FR-1 |
| Engineering Engine Provider documented without premature framework | Pass | ADP-013 Appendix B, [Platform Architecture](Platform_Architecture.md) |
| Architecture review approved | **Pending** | Human review |

## Phase 1 Spike Findings

### KiCad 10.0.4 (macOS)

- `kicad-cli pcb export` — no DSN subcommand
- `kicad-cli pcb import` — no SES/Specctra format
- `kicad-cli pcb drc` — available for post-route validation
- DSN/SES automation requires **pcbnew** (embedded KiCad Python)

### Freerouting

- CLI batch mode: `-de` / `-do` / `-inc` confirmed in upstream documentation
- Requires independently installed JAR or native executable
- Java runtime required for JAR distribution

## Implementation Delivered

| Component | Location |
|-----------|----------|
| Engine-independent contracts | `src/routing/` |
| Freerouting provider | `src/routing/freerouting.py` |
| CLI resolution | `src/utils/freerouting_cli.py` |
| DSN/SES host adapters | `src/context/dsn_export.py`, `ses_import.py` |
| Checkpoint workflow | `src/context/routing_checkpoint.py` |
| EIE orchestration | `src/inference/routing.py` |
| Routing policy (Phase 3) | `src/routing/policy.py` |
| AI prompts (Phase 4) | `src/prompts/templates/routing_policy.py`, `post_route_review.py` |
| Tests | `tests/routing/`, `tests/context/test_*routing*`, `tests/inference/test_routing.py` |

## Recommended Next Steps

1. Human architecture review approval
2. End-to-end test with Freerouting installed + pcbnew available
3. Optional routing UI tab in Assistant shell
4. Live DRC execution via `kicad-cli pcb drc` post-route
5. Routing policy persistence decision (not EKM — separate lifecycle review)

## Parent

- [ADP-013: Routing Abstraction](ADP-013-Routing-Abstraction.md)
