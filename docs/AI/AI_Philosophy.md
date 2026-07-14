# AI Philosophy

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [AI Engineering Handbook](README.md) › AI Philosophy


## Purpose

This document defines the core philosophy for using AI tools within projects that adopt the Engineering Documentation Framework.

AI is treated as an engineering assistant, not an autonomous owner of software quality, architecture, security, or production decisions.

## Primary Principle

Use the least expensive AI that can comfortably solve the task.

This does not mean always using the cheapest model. It means choosing the tool that provides the best overall engineering value after considering:

- task complexity
- required reasoning depth
- context size
- privacy requirements
- model capability
- developer time
- risk of rework
- cost of mistakes

Saving a small amount of API cost is not useful if it causes hours of additional engineering time or leads to poor design decisions.

## Human Ownership

Human developers remain responsible for all final engineering outcomes.

AI may assist with:

- brainstorming
- architecture analysis
- requirements refinement
- code generation
- documentation drafting
- testing suggestions
- debugging support
- review assistance

Humans remain responsible for:

- final engineering judgment
- security decisions
- production approval
- correctness verification
- maintainability
- testing
- release decisions

## Documentation as AI Context

AI performance improves when the project has well-structured documentation.

The repository should be treated as the source of truth. AI assistants should be pointed to authoritative documents such as:

- `PROJECT_INDEX.md`
- `PROJECT_CHARTER.md`
- `ARCHITECTURE_DECISIONS.md`
- relevant specifications
- relevant architecture documents
- relevant API, database, deployment, or development guides

AI should not be given the entire repository blindly when a smaller, better-curated context is sufficient.

## Same Standards as Human Work

AI-generated work must meet the same standards as human-written work.

AI-generated code and documentation should be:

- reviewed
- tested
- verified
- kept consistent with project architecture
- committed through the normal Git workflow
- documented when it affects architecture, behavior, or operations

## Decisions Still Require Documentation

Significant architecture decisions influenced by AI still require formal documentation.

Use ADRs for decisions that affect:

- system structure
- technology choices
- database architecture
- API design
- security model
- deployment architecture
- long-term maintainability

## KiCad AI Integration

For in-KiCad AI analysis, the human engineer remains responsible for:

- approving what project data is sent to cloud providers
- reviewing AI circuit recommendations against ERC/DRC results and datasheets
- validating AI-generated KiCad Python scripts before execution in a live project

AI acts as an engineering assistant inside KiCad — not an autonomous design authority. See [Security](./Security.md) and [Software Architecture](../Architecture/KiCad_AI_Integration_Software_Architecture.md).

## Related Documents

- [AI_Roles.md](./AI_Roles.md)
- [AI_Decision_Matrix.md](./AI_Decision_Matrix.md)
- [Governance.md](./Governance.md)

## Parent

- [AI Engineering Handbook](README.md)
