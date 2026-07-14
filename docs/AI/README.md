# AI Engineering Handbook

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › AI Engineering Handbook

This directory contains AI engineering guidance for KiCad AI Integration — covering repository development with Cursor and in-KiCad circuit analysis with Claude Sonnet 3.5.

## KiCad AI Integration Context

This project uses AI in two distinct contexts:

- **Repository development** — Cursor + Composer 2.5 for code, documentation, and tests in this Git repository
- **In-KiCad analysis** — Claude Sonnet 3.5 via the Anthropic API for circuit review with automatic project context extraction

See [Software Architecture](../Architecture/KiCad_AI_Integration_Software_Architecture.md) for the runtime architecture.

## Purpose

The AI Engineering Handbook defines:

- how AI tools support engineering work
- which tools are best suited for different tasks
- how to choose between local and cloud models
- how to control AI-related cost
- how to provide useful context to AI assistants
- how to verify AI-generated work
- how to preserve human accountability
- how AI assistants work directly on the local repository through Cursor (Composer 2.5 standard) or VS Code

## Core Principle

Use the least expensive AI that can comfortably solve the task.

Developer productivity is part of the cost equation.

Saving a small amount of model usage cost is not worthwhile if it creates hours of additional engineering effort, confusion, or rework.

## Handbook Documents

| Document | Purpose |
|---|---|
| [AI_Philosophy.md](./AI_Philosophy.md) | Core principles for AI-assisted engineering |
| [AI_Roles.md](./AI_Roles.md) | Responsibilities of Cursor + Composer 2.5, VS Code + Copilot, Continue, Ollama, cloud models, and the human developer |
| [AI_Decision_Matrix.md](./AI_Decision_Matrix.md) | Guidance for selecting the right AI tool for a task |
| [Cost_Optimization.md](./Cost_Optimization.md) | Strategy for balancing model cost, capability, and developer time |
| [Prompting_Guide.md](./Prompting_Guide.md) | Prompting practices for engineering work |
| [Context_Checklist.md](./Context_Checklist.md) | Checklist for preparing useful AI context |
| [Repository_Workflow.md](./Repository_Workflow.md) | Standard workflow for AI-assisted work in the local repository |
| [Verification.md](./Verification.md) | How to review and validate AI-generated work |
| [Security.md](./Security.md) | Security and privacy rules for AI usage |
| [Governance.md](./Governance.md) | Human accountability and documentation governance |

## Parent

- [Project Index](../../PROJECT_INDEX.md)

## Related Documents

- [Software Architecture](../Architecture/KiCad_AI_Integration_Software_Architecture.md)
- [Developer Handbook](../Developer_Handbook/README.md)
- [Governance](../Governance/README.md)
