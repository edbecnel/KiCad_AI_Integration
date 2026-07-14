# AI Roles

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [AI Engineering Handbook](README.md) › AI Roles


## Purpose

This document defines the primary roles of AI tools within the Engineering Documentation Framework.

AI-assisted engineering happens directly in the local repository through IDE-integrated assistants. Different tools have different strengths. The goal is to select the tool that fits the task rather than using one model or product for everything.

## Cursor + Composer 2.5 (standard) — Primary Repository Assistant

### Primary Role

Cursor with **Composer 2.5 (standard)** is the primary AI environment for documentation and multi-file implementation work.

It operates directly on the local Git working tree and is best suited for coordinated changes across the repository.

### Default Model

Use **Composer 2.5 (standard)** as the default Cursor model unless a task clearly requires escalation to a stronger reasoning model.

### Typical Responsibilities

- reading and modifying documentation
- multi-file feature implementation
- large refactoring tasks
- cross-file updates
- project-wide code generation
- applying coordinated code changes
- test generation
- code modernization
- navigation and cross-link updates
- running validation and reviewing results

### Best Used When

- implementing planned features
- modifying multiple related files
- updating documentation architecture
- performing project-wide changes
- working on EDF framework maintenance

## Visual Studio Code + GitHub Copilot — Primary VS Code Assistant

### Primary Role

GitHub Copilot provides AI assistance directly within Visual Studio Code on the local repository.

It is the primary AI tool for developers who work in VS Code rather than Cursor.

### Typical Responsibilities

- inline code completion and suggestions
- explaining selected code
- answering programming questions within the open project
- refactoring individual functions or files
- writing unit tests
- debugging support
- interactive development assistance
- documentation drafting in context

### Best Used When

- working within the currently open project in VS Code
- exploring unfamiliar code
- iterating on individual files or components
- asking implementation-specific questions with repository context

## Visual Studio Code + Continue — Interactive Coding Assistant

### Primary Role

Continue provides an interactive AI assistant directly within Visual Studio Code.

It is intended for focused development tasks, code understanding, and iterative problem solving while working inside a specific project.

Depending on task complexity, Continue may use either a local Ollama model or a cloud model such as Claude Sonnet.

### Typical Responsibilities

- explaining code
- answering programming questions
- reviewing selected code
- refactoring individual functions
- writing unit tests
- debugging
- interactive development assistance

### Best Used When

- working within the currently open project
- exploring unfamiliar code
- iterating on individual files or components
- asking implementation-specific questions
- privacy-sensitive work with local models

## Local Ollama — Private, Low-Cost AI

### Primary Role

Ollama provides local AI inference without requiring Internet access or API costs.

It is intended for routine development tasks where privacy, speed, or operating cost are more important than advanced reasoning.

### Typical Responsibilities

- code explanation
- documentation
- JSON generation
- Markdown editing
- README updates
- small refactoring tasks
- learning unfamiliar code
- offline development

### Advantages

- no API cost
- private execution
- works offline
- fast response time
- ideal for routine development support

### Limitations

- smaller context window
- less capable reasoning than premium cloud models
- not recommended for large multi-file architecture or complex design problems

## Claude Sonnet — Cloud Reasoning and Code Review

### Primary Role

Claude Sonnet is a preferred cloud model for difficult coding, architecture, debugging, review, and cross-file reasoning tasks when used through an IDE-integrated assistant.

Use the latest generally available Claude Sonnet model unless a project-specific reason is documented for using a different version.

### Best Used For

- architecture
- complex debugging
- cross-file reasoning
- code reviews
- large refactoring
- difficult implementation tasks

## GPT-5 Reasoning — Exceptional Engineering Problems

### Primary Role

GPT-5 reasoning should be reserved for exceptionally difficult engineering problems where deeper reasoning, careful trade-off analysis, or complex planning is justified.

### Best Used For

- hard architecture problems
- complex debugging where cheaper tools failed
- high-impact design reviews
- deep trade-off analysis
- difficult project planning decisions

## Codex — High-Value Agentic Implementation

### Primary Role

Codex should be used only when its capabilities are justified by the value and complexity of the implementation task.

### Best Used For

- high-value agentic implementation
- complex code generation
- coordinated changes with strong verification requirements

## Human Developer — Final Engineering Judgment

### Primary Role

AI assists the development process but does not replace engineering judgment.

The human developer remains responsible for all final technical decisions.

### Responsibilities

- evaluate AI-generated recommendations
- verify correctness
- review security implications
- validate architecture
- approve implementation decisions
- ensure maintainability
- perform final testing
- accept responsibility for released software

AI should be viewed as an engineering assistant rather than an autonomous software engineer. Final responsibility for software quality, security, correctness, and long-term maintainability always remains with the developer.

## KiCad AI Integration Roles

| Role | Context | Responsibility |
|------|---------|----------------|
| Cursor + Composer 2.5 | Repository development | Code, docs, tests in `src/` |
| Claude Sonnet 3.5 | In-KiCad analysis | Circuit review via Anthropic API |
| Human engineer | Both contexts | Approve cloud transmission, verify recommendations, run scripts safely |

Integration guides: [Developer Handbook](../Developer_Handbook/README.md).

## Related Documents

- [AI_Philosophy.md](./AI_Philosophy.md)
- [AI_Decision_Matrix.md](./AI_Decision_Matrix.md)
- [Repository_Workflow.md](./Repository_Workflow.md)
- [Verification.md](./Verification.md)

## Parent

- [AI Engineering Handbook](README.md)
