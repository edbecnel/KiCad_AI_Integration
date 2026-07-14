# Context Checklist

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [AI Engineering Handbook](README.md) › Context Checklist


## Purpose

This document defines the information that should be provided to AI assistants when performing engineering work.

The goal is to provide enough context for useful output without overwhelming the assistant with unrelated files.

## Core Checklist

Before asking AI to perform engineering work, identify:

- relevant requirements
- applicable ADRs
- relevant architecture documents
- relevant specifications
- coding standards
- only the files required for the task
- clear success criteria
- known constraints
- expected output format
- whether the work is planning, editing, implementation, review, or troubleshooting

## Repository Entry Points

When starting a new AI session, useful entry points include:

- `PROJECT_INDEX.md`
- `PROJECT_CHARTER.md`
- `ARCHITECTURE_DECISIONS.md`
- `docs/Architecture/`
- `docs/Specifications/`
- `docs/Development/`
- `docs/Developer_Handbook/`
- `docs/AI/`

## Avoid Overloading Context

Do not provide the entire repository unless the task genuinely requires it.

Prefer targeted context:

- the affected file
- related specification
- related architecture document
- relevant tests
- relevant ADRs
- relevant API or database documentation

## For Documentation Tasks

Provide:

- target document path
- purpose of the document
- audience
- related documents
- preferred tone
- whether to create, update, split, merge, or review

## For Coding Tasks

Provide:

- current behavior
- desired behavior
- relevant files
- relevant tests
- error messages or logs
- constraints
- acceptance criteria

## For Architecture Tasks

Provide:

- project goals
- constraints
- current architecture
- alternatives considered
- non-functional requirements
- known risks
- affected systems

## KiCad Project Context

When preparing AI context for circuit analysis, include only what the audit requires:

- active schematic and PCB data
- netlist and BOM
- ERC and DRC results
- design intent text from the user
- selected objects when doing focused review

Authoritative architecture: [Software Architecture](../Architecture/KiCad_AI_Integration_Software_Architecture.md).

Avoid sending full S-expression files when summarized JSON extraction is sufficient.

## Related Documents

- [Prompting_Guide.md](./Prompting_Guide.md)
- [AI_Decision_Matrix.md](./AI_Decision_Matrix.md)
- [Verification.md](./Verification.md)

## Parent

- [AI Engineering Handbook](README.md)
