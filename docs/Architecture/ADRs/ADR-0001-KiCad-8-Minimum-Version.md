# ADR-0001: KiCad 8+ Minimum Version

[Home](../../../README.md) › [Project Index](../../../PROJECT_INDEX.md) › [Architecture](../README.md) › [ADRs](README.md) › ADR-0001

## Status

Accepted

## Date

2026-07-14

## Decision Owners

- Project maintainers

## Context

KiCad AI Integration runs Python scripts inside KiCad's embedded interpreter using `pcbnew`, schematic APIs, and wxPython for UI components. KiCad's Python scripting surface and schematic access APIs vary across major versions.

The project needs a clear minimum supported version for:

- Developer environment documentation
- Integration testing expectations
- API assumptions in the Context Collection Engine

## Decision

Target **KiCad 8.0 or later** as the minimum supported version for KiCad AI Integration.

Development and documentation assume:

- `import pcbnew` in the KiCad Scripting Console
- wxPython available for in-KiCad UI dialogs
- Schematic access APIs available for the target KiCad version

## Alternatives Considered

### KiCad 7.x support

- Advantages: Broader user base on older installs
- Disadvantages: API differences increase maintenance; schematic scripting support less consistent
- Reason not selected: KiCad 8 provides a stable baseline for Python integration work

### KiCad 9+ only

- Advantages: Latest APIs only
- Disadvantages: Excludes users on KiCad 8; premature while project is in planning
- Reason not selected: KiCad 8 is sufficient for Phase 1 MVP scope

## Consequences

### Positive

- Clear prerequisite in [Development Environment](../../Developer_Handbook/01_Development_Environment.md)
- Simpler testing matrix for Phase 1
- Aligns with current developer handbook documentation

### Negative

- Users on KiCad 7 or earlier cannot use the integration without upgrading

### Risks

- Schematic API gaps on specific KiCad 8 minor releases — mitigate by documenting tested version in release notes

## Implementation Notes

- Document minimum version in README and Developer Handbook
- Confirm `pcbnew` and schematic APIs during Phase 0 exit criteria in [Master Task List](../../../tasks/MASTER_TASK_LIST.md)

## References

- [Development Environment](../../Developer_Handbook/01_Development_Environment.md)
- [Software Architecture](../KiCad_AI_Integration_Software_Architecture.md)

## Parent

- [Architecture Decision Records](README.md)
