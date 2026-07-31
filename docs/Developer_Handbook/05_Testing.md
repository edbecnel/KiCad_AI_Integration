# Testing

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Developer Handbook](README.md) › Testing

## Purpose

Testing strategy and conventions for KiCad AI Integration. A clear testing standard supports reliable refactors — including AI-assisted ones — and defines what "done" means for each change.

## When to use it

- Implementing features in `src/` — write tests in the same change set as production code
- Fixing bugs — add a regression test that fails before the fix
- AI-assisted development — require AI-generated code to include tests meeting this bar
- Release readiness — confirm test gates before tagging a release

## Testing philosophy

| Principle | Description |
|-----------|-------------|
| Test behavior, not implementation | Tests should survive internal refactors |
| Pyramid balance | Many unit tests, fewer integration, minimal manual E2E |
| Fast feedback | Unit tests run without KiCad installed |
| Deterministic | No flaky tests |
| Readable tests | Arrange–Act–Assert structure |

## Test levels

### Unit tests

**Scope:** Context model, prompt assembly, provider layer with mocked HTTP.

**Location:** `tests/`

**Run:** `pytest` from repository root — no KiCad required.

Planned coverage:

- Context model serialization and deserialization
- Prompt assembly from fixtures — golden-file snapshots
- Provider layer with mocked Anthropic API responses

### Integration tests

**Scope:** File-based pipeline from fixture KiCad files through context and prompt building.

**Location:** `tests/` with fixtures under `examples/`

**Fixtures:** Sample `.kicad_sch`, `.kicad_pcb`, and netlist files.

### End-to-end — manual (external scripts)

**Scope:** Run `scripts/run_ai_assistant.py` against a saved `.kicad_pro` from Terminal; exercise chat, AERF, and Notebook UIs with Approve & Send gates.

**When:** Phase 1 MVP validation; document steps in PR test plan.

**Entry points:**

- [Testing With Your KiCad Project](../User_Guides/Testing_With_Your_KiCad_Project.md) — end-user walkthrough
- [07_E2E_Full_Flow.md](07_E2E_Full_Flow.md) — contributor checklists
- [06_E2E_Chat_UI.md](06_E2E_Chat_UI.md) — chat-specific checklist

KiCad Scripting Console is an alternative launch path; file-based context does not require `pcbnew`.

### Mocking pcbnew

Unit tests outside KiCad use mocked `pcbnew` objects and file-based fixtures. See [Master Task List](../../tasks/MASTER_TASK_LIST.md) § Testing and CI.

## Coverage expectations

| Area | Target | Enforced in CI |
|------|--------|----------------|
| Context model and prompts | High coverage before Phase 1 release | Planned |
| Provider layer | Mocked API tests required | Planned |
| wxPython UI | Manual E2E primarily | No |

## Golden-file prompt snapshots

Store expected prompt output for fixture projects to catch regressions in prompt assembly. Update snapshots only when prompt format changes intentionally.

## Related Documents

- [02_AI_Development.md](02_AI_Development.md)
- [Development Environment](01_Development_Environment.md)
- [E2E Full Flow](07_E2E_Full_Flow.md)
- [Testing With Your KiCad Project](../User_Guides/Testing_With_Your_KiCad_Project.md)
- [Master Task List](../../tasks/MASTER_TASK_LIST.md) § Testing and CI
- [Verification](../AI/Verification.md)

## Parent

- [Developer Handbook](README.md)
