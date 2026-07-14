# Verification

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [AI Engineering Handbook](README.md) › Verification


## Purpose

This document defines how AI-generated work should be reviewed and validated.

AI output should never be accepted blindly. It must be verified according to the same standards as human-generated work.

## General Verification Rules

AI-generated work should be checked for:

- correctness
- completeness
- security implications
- consistency with architecture
- consistency with documentation
- maintainability
- test coverage
- formatting and style
- broken links
- unintended file changes

## Code Verification

When reviewing AI-generated code:

- read the diff carefully
- run relevant tests
- inspect error handling
- verify data validation
- check security-sensitive logic
- confirm naming and style consistency
- ensure no secrets were introduced
- verify dependency changes
- confirm performance implications when relevant

## Documentation Verification

When reviewing AI-generated documentation:

- confirm facts against the implementation
- verify links
- check that authoritative sources remain clear
- remove duplication
- ensure terminology is consistent
- update `PROJECT_INDEX.md` when major documents are added or moved
- ensure outdated content is archived or clearly replaced

## Architecture Verification

When AI influences architecture:

- review trade-offs
- document significant decisions in ADRs
- confirm alternatives were considered
- validate assumptions
- check long-term maintainability
- confirm operational implications

## Git Verification

Before committing AI-generated changes:

- inspect `git status`
- review the full diff
- confirm no unrelated files changed
- confirm no files were accidentally deleted
- confirm generated files are intentional
- run tests when applicable

## KiCad-Specific Verification

When reviewing AI circuit analysis output:

- cross-check recommendations against ERC and DRC results
- verify component ratings against BOM datasheet fields
- validate AI-generated KiCad Python scripts in the Scripting Console before production use
- compare netlist consistency with schematic connectivity
- verify AI-inferred netlist gap-fill output against ERC, DRC, and the schematic before applying any connectivity changes — see [Netlist Gap Fill](../Specifications/Netlist_Gap_Fill.md)
- verify AI-generated `.lib`/`.SUBCKT` models against datasheet (when resolved) and KiCad symbol pin order before simulation
- treat context-synthesized and last-resort inferred models as drafts requiring datasheet or bench verification

## Related Documents

- [Governance.md](./Governance.md)
- [Security.md](./Security.md)
- [AI_Philosophy.md](./AI_Philosophy.md)
- [Netlist Gap Fill](../Specifications/Netlist_Gap_Fill.md)

## Parent

- [AI Engineering Handbook](README.md)
