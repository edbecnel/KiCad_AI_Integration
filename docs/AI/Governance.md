# AI Governance

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [AI Engineering Handbook](README.md) › AI Governance


## Purpose

This document defines governance expectations for AI-assisted engineering work.

AI can accelerate software development, but human developers remain accountable for all engineering outcomes.

## Human Accountability

Human developers are responsible for:

- final engineering judgment
- security approval
- production approval
- architectural ownership
- accepting or rejecting AI-generated changes
- validating correctness
- ensuring maintainability

AI should propose, draft, analyze, and assist. It should not silently own decisions.

## Documentation Synchronization

When implementation changes affect documented behavior, update the relevant documentation.

Documentation updates should be included in the same commit or pull request whenever practical.

## Architecture Decisions

Significant technical decisions should be recorded in ADRs even when AI helped produce the analysis.

Use ADRs for decisions involving:

- technology selection
- system structure
- database design
- API design
- deployment architecture
- security model
- major trade-offs

## Single Source of Truth

Avoid creating duplicate explanations across multiple documents.

If information already exists elsewhere:

- link to it
- summarize briefly if needed
- do not copy the full content unnecessarily

## PROJECT_INDEX Maintenance

`PROJECT_INDEX.md` is the primary navigation hub.

Update it when:

- major documents are created
- major documents are moved
- documentation domains are added
- authoritative documents change
- project priorities change

## Future Governance Direction

A future version of the Engineering Documentation Framework may include machine-readable AI agent rules for Cursor, VS Code, Continue, and other AI tools.

Those rules should help AI assistants automatically maintain documentation consistency, cross-references, architecture decisions, and project indexes without requiring the developer to repeat the same instructions every time.

## KiCad AI Integration

Human engineers must review and approve:

- AI-generated KiCad Python scripts before running them against live projects
- cloud transmission of schematic, PCB, and BOM data
- AI circuit recommendations before acting on design changes

Documentation governance for this project follows [Governance](../Governance/README.md).

## Related Documents

- [AI_Philosophy.md](./AI_Philosophy.md)
- [Verification.md](./Verification.md)
- [Security.md](./Security.md)
- [Governance](../Governance/README.md)

## Parent

- [AI Engineering Handbook](README.md)
