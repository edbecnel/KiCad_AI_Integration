# Contributing to KiCad AI Integration

Thank you for contributing. This project implements an AI-assisted engineering reasoning platform (AERP) with KiCad as the first host.

## Getting started

1. Read [First-Time Setup](docs/Developer_Handbook/00_First_Time_Setup.md)
2. Run tests: `pytest` from the repository root (KiCad not required)
3. Review [Feature Overview](docs/User_Guides/Feature_Overview.md) for capability boundaries

## Pull request workflow

1. Fork or branch from `main`
2. Make focused changes with tests where behavior changes
3. Run `pytest` locally before opening a PR
4. Update [MASTER_TASK_LIST](tasks/MASTER_TASK_LIST.md) and [Feature Overview](docs/User_Guides/Feature_Overview.md) when completing milestones
5. Open a PR with a clear summary and test plan

## Coding standards

- Match existing style in the module you edit
- **Platform import boundary:** modules under `src/providers/`, `src/prompts/`, `src/inference/`, `src/reasoning/`, `src/ekm/`, `src/platform_core/` must not import KiCad parsers, `pcbnew`, or wxPython
- Host integration lives in `src/context/`, `src/ui/`, and `scripts/`
- Prefer file-based KiCad parsing for CI-testable extractors; live `pcbnew` APIs belong in Phase 1.5+

## Tests

- Unit and integration tests run without KiCad: `pytest`
- Use `AppConfig(artifact_library_path=tmp_path / "library")` in tests that touch the datasheet resolver
- Golden prompt snapshots live under `tests/prompts/golden/` and `tests/context/golden/`

## Documentation

- User-facing capability status: [Feature Overview](docs/User_Guides/Feature_Overview.md)
- Implementation backlog: [MASTER_TASK_LIST](tasks/MASTER_TASK_LIST.md)
- Architecture changes: add or update ADRs/ADPs under `docs/Architecture/`

## Security

- Never commit API keys or credentials
- See [AI Security](docs/AI/Security.md) for data-handling expectations
