# Platform Backlog (Post Sprint 12)

[Home](../README.md) · [Project Index](../PROJECT_INDEX.md) · [Master Task List](../tasks/MASTER_TASK_LIST.md)

Tracked platform and product gaps deferred after Sprint 12. See [`tasks/MASTER_TASK_LIST.md`](../tasks/MASTER_TASK_LIST.md) for authoritative checkboxes.

## Near-term product

| Item | Notes |
|------|-------|
| Notebook AI edit proposals | EKM View Model exists; AI-driven edits not wired |
| Additional circuit families | Beyond Blocking Oscillator + Generic scaffold |
| Project-wide datasheet force-refresh | Partial — failed URLs only today |
| Routing candidate diff polish | Side-by-side dialog shipped; richer diff metrics TBD |

## Security and housekeeping

| Item | Notes |
|------|-------|
| `--ask` CLI approval gate | Dev bypass lacks explicit approval |
| Context redaction | Exclude paths, obfuscate project name |
| `.gitignore` for secrets | Config files with API keys |
| Credential storage audit | Partial — documented in Security.md |

## Deferred

| Item | Notes |
|------|-------|
| True wxAUI dock in PCB editor | ADP-011 Phase 2 |
| Clickable component refs in AI responses | R1 → highlight in KiCad |
| `HostLink` beyond `KiCadLink` | ADP-009 — second host |
| Local-model / air-gapped path | Ollama, etc. |

## Human-only validation

Manual KiCad chat + Freerouting E2E — [`Manual_Validation_Checklist.md`](Developer_Handbook/Manual_Validation_Checklist.md). **Not auto-completable by agents.**
