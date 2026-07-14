# Cost Optimization

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [AI Engineering Handbook](README.md) › Cost Optimization


## Purpose

This document defines the cost optimization strategy for AI-assisted software development.

The objective is not to minimize API cost at all costs. The objective is to minimize total development cost, including developer time, rework, risk, and quality.

## Core Principle

Use the least expensive AI that can comfortably solve the task.

A cheap tool is not actually cheap if it creates confusion, poor design, inaccurate code, or hours of manual correction.

## Cost Factors

When choosing an AI tool, consider:

- model usage cost
- developer time
- task complexity
- context size
- risk of incorrect output
- security and privacy requirements
- likelihood of rework
- importance of the decision
- cost of downstream mistakes

## Recommended Progression

Use this progression unless a project-specific reason justifies a different choice:

1. Local model such as Qwen 14B for routine tasks
2. Cursor + Composer 2.5 (standard) for everyday multi-file documentation and implementation
3. Low-cost cloud model for simple tasks that do not require advanced reasoning
4. Claude Sonnet for complex coding, review, debugging, and cross-file reasoning
5. GPT-5 reasoning for exceptionally difficult engineering problems
6. Codex for high-value agentic implementation tasks

## When to Use Local AI

Use local AI when:

- privacy matters
- offline work is needed
- the task is routine
- the context is small
- the task involves Markdown, JSON, or simple code explanation
- cost should be near zero

## When to Pay for a Stronger Model

Use a stronger cloud model when:

- the task spans multiple files
- architecture is involved
- the decision is high impact
- debugging is difficult
- cheaper models have failed
- incorrect output would create significant rework
- the model can save meaningful developer time

## Avoid False Economy

Do not spend an hour trying to save a few cents.

Developer time is part of the cost equation. A more capable model is often justified when it avoids:

- architectural mistakes
- implementation churn
- repeated failed attempts
- misunderstanding of requirements
- poor documentation structure
- security mistakes

## KiCad Token Budgeting

Large KiCad projects can produce oversized prompts. Before calling the Anthropic API:

- summarize long net lists and trace data
- omit S-expression noise from raw file dumps
- use partial context flags — PCB-only, schematic-only, critical-nets-only
- display token usage metadata for cost visibility in Phase 2

See [Software Architecture](../Architecture/KiCad_AI_Integration_Software_Architecture.md) for the Project Context Model design.

## Related Documents

- [AI_Philosophy.md](./AI_Philosophy.md)
- [AI_Decision_Matrix.md](./AI_Decision_Matrix.md)

## Parent

- [AI Engineering Handbook](README.md)
