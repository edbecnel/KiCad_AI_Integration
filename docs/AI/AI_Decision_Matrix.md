# AI Decision Matrix

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [AI Engineering Handbook](README.md) › AI Decision Matrix


## Purpose

This document helps developers choose the appropriate AI tool for a software engineering task.

All work happens in the local repository through IDE-integrated assistants. The recommended approach is to start with the least expensive tool that can comfortably solve the problem, then escalate only when needed.

## Roles Across the Software Development Lifecycle

| SDLC stage | Primary AI | Secondary AI | Typical use cases |
|---|---|---|---|
| Vision and product ideas | Cursor + Composer 2.5 | Claude Sonnet | Brainstorming, feature ideas, market analysis |
| Requirements analysis | Cursor + Composer 2.5 | Claude Sonnet | Functional requirements, user stories, acceptance criteria |
| Architecture and system design | Cursor + Composer 2.5 | Claude Sonnet | System architecture, technology selection, trade-off analysis |
| Database design | Cursor + Composer 2.5 | Claude Sonnet | Entity modeling, normalization, indexing strategies |
| API design | Cursor + Composer 2.5 | Claude Sonnet | REST APIs, validation rules, security, versioning |
| Project planning | Cursor + Composer 2.5 | Claude Sonnet | Roadmaps, milestones, task decomposition |
| Documentation | Cursor + Composer 2.5 | VS Code + Copilot | Markdown, developer guides, user documentation |
| Single-file coding | VS Code + Copilot | VS Code + Qwen 14B | Explain code, small edits, documentation, local/private code |
| Multi-file coding | Cursor + Composer 2.5 | VS Code + Copilot | Feature implementation, coordinated changes across multiple files |
| Complex implementation | Claude Sonnet | Cursor + Composer 2.5 | Difficult algorithms, architectural refactoring, advanced debugging |
| Code review | Claude Sonnet | Cursor + Composer 2.5 | Review design, identify bugs, improve maintainability |
| Testing | Cursor + Composer 2.5 | Claude Sonnet | Unit tests, integration tests, test coverage |
| Deployment | Cursor + Composer 2.5 | Claude Sonnet | CI/CD, deployment scripts, release documentation |
| Final engineering review | Human Developer | Cursor + Composer 2.5 | Final design validation and engineering judgment |

## General Tool Selection

| If you need to... | Recommended tool |
|---|---|
| Brainstorm products, requirements, architecture, APIs, or databases | Cursor + Composer 2.5 |
| Explain or refactor a single file in VS Code | VS Code + GitHub Copilot |
| Work with sensitive or private code | VS Code + Continue + Qwen 14B |
| Understand multiple files or perform complex debugging | VS Code + Continue + Claude Sonnet |
| Implement features spanning multiple files | Cursor + Composer 2.5 |
| Rapid multi-file implementation | Cursor + Composer 2.5 |
| Perform code reviews | Claude Sonnet |
| Produce technical documentation | Cursor + Composer 2.5 |
| Make the final engineering decision | Human Developer |

## Cursor + Composer 2.5 (standard)

Use Cursor with **Composer 2.5 (standard)** as the default model for repository work in Cursor.

### Good Fit

- documentation updates
- multi-file implementation
- navigation and cross-link maintenance
- coordinated refactors
- framework maintenance
- validation-driven corrections

### Advantages

- operates directly on the local working tree
- strong multi-file coordination
- good default balance of capability and cost for everyday engineering work

### When to Escalate

Escalate to Claude Sonnet or another stronger model when Composer 2.5 has failed on a difficult problem or the task requires unusually deep reasoning.

## VS Code + GitHub Copilot

Use GitHub Copilot when working in Visual Studio Code on routine development tasks with repository context.

### Good Fit

- inline code completion
- explaining existing code
- learning an unfamiliar file
- small refactoring
- simple bug fixes
- unit test generation
- documentation within the open project

### Advantages

- integrated with VS Code
- operates on the local working tree
- low friction for single-file work

### Limitations

- weaker than agentic tools for large coordinated changes
- may struggle with complex multi-file architecture

## VS Code + Qwen 14B

Use VS Code + Qwen 14B when working on routine, local, or privacy-sensitive tasks.

### Good Fit

- explaining existing code
- learning an unfamiliar file
- writing Markdown
- creating JSON
- updating README files
- small refactoring
- simple bug fixes
- unit test generation
- working offline
- working with sensitive or proprietary code

### Advantages

- free after installation
- runs locally
- fast response time
- no Internet required
- no API cost

### Limitations

- smaller context window
- weaker reasoning
- not suitable for large multi-file projects
- may struggle with complex architecture

## VS Code + Claude Sonnet

Use VS Code + Claude Sonnet when stronger reasoning or broader context is required.

### Good Fit

- working across multiple files
- understanding a large codebase
- designing new features
- performing architectural refactoring
- debugging difficult problems
- reviewing pull requests
- evaluating design alternatives
- implementing complex business logic

### Advantages

- excellent reasoning
- strong architectural understanding
- large effective context window
- high-quality code reviews

### Trade-Offs

- requires Internet access
- API usage costs money
- should be reserved for problems where the additional capability provides clear value

## Escalation Strategy

Start with the lowest-cost tool that is likely to solve the task successfully.

Recommended progression:

1. VS Code + GitHub Copilot or Qwen 14B for routine single-file work
2. Cursor + Composer 2.5 (standard) for multi-file documentation and implementation
3. Claude Sonnet for stronger reasoning, large context, and code review
4. GPT-5 reasoning for exceptionally difficult engineering problems
5. Codex only when high-value agentic implementation is justified

## KiCad AI Integration

| Task | Recommended tool |
|------|-----------------|
| Repository code and documentation | Cursor + Composer 2.5 |
| In-KiCad circuit review with project context | Claude Sonnet 3.5 via in-KiCad script |
| Sensitive schematic data, air-gapped workflow | Local Ollama — future provider support |
| KiCad Python script development | Cursor + Composer 2.5, test in KiCad Scripting Console |

See [AI Tools for Advanced Circuit Analysis](../Reference/AI_Tools_for_Advanced_Circuit_Analysis.md) for external tool comparisons.

## Related Documents

- [AI_Roles.md](./AI_Roles.md)
- [Repository_Workflow.md](./Repository_Workflow.md)
- [Cost_Optimization.md](./Cost_Optimization.md)
- [Context_Checklist.md](./Context_Checklist.md)

## Parent

- [AI Engineering Handbook](README.md)
