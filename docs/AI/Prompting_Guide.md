# Prompting Guide

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [AI Engineering Handbook](README.md) › Prompting Guide


## Purpose

This document provides practical prompting guidance for engineering work.

Good prompts reduce ambiguity, improve AI output quality, and help keep documentation and implementation aligned.

## General Prompting Principles

- Start with the smallest amount of context necessary.
- Reference `PROJECT_INDEX.md` and relevant specifications.
- Identify the target files or folders when possible.
- State the desired output format.
- Ask for trade-off analysis before implementation.
- Keep documentation and code synchronized.
- Verify all AI-generated output before committing.

## Provide Clear Context

When asking an AI assistant to work on a project, include:

- project goal
- relevant files
- current problem
- expected outcome
- constraints
- desired style or format
- whether the assistant should edit, review, summarize, or plan

## Prefer Specific Instructions

Weak prompt:

```text
Fix the docs.
```

Better prompt:

```text
Review PROJECT_INDEX.md and README.md. Update them so they reference docs/AI/ as the authoritative AI Engineering Handbook. Do not modify unrelated files.
```

## Ask for Planning Before Large Changes

For complex work, ask the AI to summarize its plan first.

Useful pattern:

```text
Before editing, inspect the current repository structure and summarize the files you intend to modify. Wait for approval before applying changes.
```

## Require Preservation of Existing Content

When refactoring documentation, explicitly require that existing content be preserved unless intentionally removed.

Useful pattern:

```text
Refactor this document into smaller files. Do not lose information. If content is removed, explain why and where the remaining authoritative version lives.
```

## Use Documentation Domains

When asking AI to create or move documentation, reference the framework domains:

- Architecture
- AI
- Development
- Specifications
- API
- Database
- Deployment
- User Guides
- Reference
- Templates
- Archive

## Recommended Workflow Prompts

### New Feature

1. Define requirements in the local repository.
2. Review architecture with Cursor (Composer 2.5) when needed.
3. Record important decisions in `ARCHITECTURE_DECISIONS.md`.
4. Implement with Cursor (Composer 2.5) or VS Code + GitHub Copilot.
5. Escalate to Claude Sonnet only when stronger reasoning is required.
6. Review, test, and commit.

### Existing Code Investigation

1. Begin with VS Code + Copilot or Continue + local AI.
2. Escalate to Claude Sonnet for multi-file reasoning.
3. Document important findings in the repository.

### Documentation

1. Draft with Cursor (Composer 2.5) in the local working tree.
2. Verify against the implementation.
3. Commit documentation with related code whenever practical.

## KiCad Circuit Analysis Prompts

For in-KiCad engineering audits, use structured prompt sections:

- `<functional_description>` — design intent and constraints
- `<kicad_python_extracted_data>` — PCB/schematic extraction JSON
- `<kicad_netlist>` — connectivity data when relevant

See [Programmatic AI Analysis Guide](../Developer_Handbook/Guide-Programmatic_AI_Analysis.md) and [KiCad Python API Scripting Guide](../Developer_Handbook/Guide-KiCad_Python_API_Custom_AI_Scripting.md).

## Related Documents

- [Context_Checklist.md](./Context_Checklist.md)
- [Verification.md](./Verification.md)
- [Governance.md](./Governance.md)

## Parent

- [AI Engineering Handbook](README.md)
