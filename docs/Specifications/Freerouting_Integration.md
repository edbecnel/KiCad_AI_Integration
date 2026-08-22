# Freerouting Integration

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Specifications](README.md) › Freerouting Integration

## Status

**Draft** — Phase 1 investigation complete; Phase 2 POC implementation in progress.

## Owner

Project maintainers

## Purpose

Define Freerouting as the **first reference implementation** of the routing abstraction defined in [ADP-013: Routing Abstraction](../Architecture/ADP-013-Routing-Abstraction.md).

Freerouting is an advanced autorouter compatible with PCB design tools that support the Specctra DSN interface. KAI orchestrates Freerouting as an independently installed external tool; KAI retains design intent, routing policy, validation, and user authority.

> **Freerouting solves routing. KAI solves PCB design intent.**

## Goals

- Provide a working `FreeroutingRoutingEngine` behind the engine-independent `RoutingEngine` contract
- Support headless routing via Freerouting CLI (`-de` / `-do` / `-inc`)
- Export DSN and import SES via KiCad host adapters (pcbnew when available)
- Treat Freerouting as an independently installed external tool
- Register routing artifacts (DSN, SES, logs) in the project artifact library
- Enforce transactional checkpoint workflow before modifying authoritative board state

## Non-Goals

- Bundling or redistributing Freerouting (out of initial scope; requires separate licensing/distribution review)
- Replacing the KiCad Freerouting plugin for interactive one-click routing
- Critical-net AI classification (Phase 4 of ADP-013)
- Closed-loop re-routing optimization (Phase 5)

## Users and Stakeholders

- PCB designers using KiCad AI Integration who want intent-aware bulk autorouting
- Developers extending KAI with additional routing engine providers

## User Experience

1. User opens a KiCad project with a placed but partially or fully unrouted PCB.
2. User invokes routing from the KAI assistant (future UI tab or CLI).
3. KAI presents routing policy summary (exclusions, preserved routes) for approval.
4. KAI creates a board checkpoint, exports routing input, invokes Freerouting, imports result to a **candidate** board copy.
5. KAI runs DRC summary and optional post-route review.
6. User accepts (promotes candidate to authoritative), rejects (discards candidate), or revises policy and re-runs.

## Functional Requirements

### FR-1: External tool detection

KAI SHALL detect whether Freerouting is installed and report:

- Not installed
- Installed but unsupported version
- Installed and capable (CLI available)

Initial integration SHALL treat Freerouting as an **independently installed external tool**. Bundling or redistribution is outside the initial scope and requires a separate licensing/distribution review.

Resolution order: explicit config path → `FREEROUTING_CLI` / `FREEROUTING_JAR` env → PATH → common install locations.

### FR-2: DSN export (host adapter)

KAI SHALL export a Specctra DSN file from the KiCad PCB for Freerouting consumption.

### FR-3: Freerouting CLI invocation

KAI SHALL invoke Freerouting in batch mode:

```bash
java -jar freerouting.jar -de <board>.dsn -do <board>.ses [-inc <net_class>...]
```

Or native Freerouting executable when available.

### FR-4: SES import (host adapter)

KAI SHALL import a Specctra SES file produced by Freerouting into a **candidate** board copy.

### FR-5: Checkpoint workflow

KAI SHALL preserve the original board state before routing and SHALL NOT modify the authoritative `.kicad_pcb` until the user explicitly accepts the routing candidate.

### FR-6: Graceful degradation

When Freerouting is not installed, KAI SHALL continue to function and report routing as unavailable.

## Non-Functional Requirements

### NFR-1: Testability without KiCad

Unit tests SHALL mock subprocess invocation and pcbnew-dependent adapters.

### NFR-2: Timeout

Routing subprocess SHALL respect configurable timeout (default 600s).

### NFR-3: Artifact provenance

DSN, SES, and routing logs SHALL be registered in `<project>/kicad_ai/exports/` with manifest entries.

## Phase 1 Findings — KiCad DSN/SES Automation

Investigation performed 2026-08-23 on KiCad **10.0.4** (macOS).

### DSN export

| Mechanism | Available? | Notes |
|-----------|------------|-------|
| `kicad-cli pcb export dsn` | **No** | `kicad-cli pcb export` subcommands (KiCad 10.0.4): gerbers, drill, step, svg, etc. — **no DSN** |
| `pcbnew` API | **Yes** (when embedded) | `pcbnew.ExportSpecctraDSN(board, path)` — used by KiCad PCB Editor File → Export → Specctra DSN |
| Freerouting KiCad plugin | **Yes** (interactive) | Plugin and Content Manager; not suitable for headless KAI automation |

**Conclusion:** KAI host adapter `src/context/dsn_export.py` SHALL use `pcbnew` when available. When `pcbnew` is unavailable (external Python / CI), DSN export returns a clear status indicating pcbnew is required. **Do not assume `kicad-cli` DSN export.**

### SES import

| Mechanism | Available? | Notes |
|-----------|------------|-------|
| `kicad-cli pcb import` (ses/specctra) | **No** | Import formats: altium, eagle, cadstar, etc. — **no SES** |
| `pcbnew` API | **Yes** (when embedded) | `pcbnew.ImportSpecctraSES(board, path)` — used by File → Import → Specctra Session File |
| Freerouting KiCad plugin | **Yes** (interactive) | Automatic import on plugin completion |

**Conclusion:** KAI host adapter `src/context/ses_import.py` SHALL use `pcbnew` when available. Fallback: document manual import steps for users running external Python without pcbnew.

### DRC after routing

| Mechanism | Available? | Notes |
|-----------|------------|-------|
| `kicad-cli pcb drc` | **Yes** | Confirmed in KiCad 10.0.4; suitable for post-route validation |
| Report file parsing | **Yes** | Existing `erc_drc_summary.py` pattern |

### Freerouting CLI

Freerouting supports headless batch routing per [upstream documentation](https://github.com/freerouting/freerouting):

- `-de [design input file]` — load Specctra DSN
- `-do [design output file]` — save Specctra SES
- `-inc [net class names]` — ignore net classes during routing

Freerouting requires Java runtime for JAR distribution. Native installers also available per platform.

### Version matrix (initial)

| Component | Minimum | Tested | Notes |
|-----------|---------|--------|-------|
| KiCad | 8.0+ ([ADR-0001](../Architecture/ADRs/ADR-0001-KiCad-8-Minimum-Version.md)) | 10.0.4 | DSN/SES via pcbnew only |
| Freerouting | TBD | Latest release | Independently installed |
| Java | 11+ (typical) | — | Required for JAR |

## Architecture Mapping

```text
Capability:              PCB Routing
Capability Abstraction:  RoutingEngine (ADP-013)
Provider:                FreeroutingRoutingEngine
Adapter:                 dsn_export.py, ses_import.py, freerouting_cli.py
External Engine:         Freerouting (independently installed)
```

### Freerouting-specific exchange (NOT in generic RoutingRequest)

```python
@dataclass
class FreeroutingExchange:
    dsn_path: Path
    ses_output_path: Path
    excluded_net_classes: list[str]  # maps from RoutingExclusions
```

`FreeroutingRoutingEngine` translates engine-independent `RoutingRequest` → `FreeroutingExchange` → subprocess → `RoutingResult`.

## POC Acceptance Criteria

- [ ] `resolve_freerouting()` locates JAR or executable; raises typed error when missing
- [ ] `export_specctra_dsn()` succeeds when pcbnew available (or returns structured unavailable status)
- [ ] `import_specctra_ses()` succeeds when pcbnew available
- [ ] `FreeroutingRoutingEngine.route()` produces SES artifact on success (mocked in CI)
- [ ] Checkpoint copy created before routing; authoritative board unchanged until accept
- [ ] Routing artifacts registered in `kicad_ai/exports/`
- [ ] `routing_enabled` config defaults to `false`

## Configuration

| Key | Default | Description |
|-----|---------|-------------|
| `freerouting_jar` | `null` | Path to `freerouting.jar` |
| `freerouting_cli` | `null` | Path to native Freerouting executable (alternative to JAR) |
| `routing_enabled` | `false` | Enable routing workflow |
| `routing_timeout_sec` | `600` | Subprocess timeout |

Environment variables: `FREEROUTING_JAR`, `FREEROUTING_CLI`.

## Risks

| Risk | Mitigation |
|------|------------|
| pcbnew unavailable in external Python | Document requirement; plugin/embedded path for full workflow |
| GPL licensing if bundling | External invocation only; no bundling in initial scope |
| Poor autorouter engineering quality | ADP-013 policy layer + post-route review; user authority |
| KiCad version API drift | Capability probing; version matrix maintenance |

## Related Documents

- [ADP-013: Routing Abstraction](../Architecture/ADP-013-Routing-Abstraction.md)
- [Platform Architecture](../Architecture/Platform_Architecture.md)
- [Freerouting upstream integrations](https://github.com/freerouting/freerouting/blob/master/docs/integrations.md)

## Parent

- [Specifications](README.md)
