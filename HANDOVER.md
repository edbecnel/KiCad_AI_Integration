```
HANDOVER — Phase 2 Sprint 4 (ADP-011 Phase D) — completed
================================================================================
Date: 2026-08-23
Repo: KiCad_AI_Integration

SUMMARY
-------
Legacy launcher dialog and modal `*_dialog.py` entry paths are removed. The unified
Assistant shell (`--ui`, ActionPlugin, `--ui-*` deep links) is the sole UI entry.
Conversation sessions persist to `<project>/kicad_ai/conversation.json` for replay/debug.
Chat conversation log shows markdown-friendly formatting plus per-turn token/cost summary.

WHAT WAS DONE
-------------
1. **Phase D cleanup** — removed `launcher_dialog.py` and modal wrappers; helpers moved to
   `src/ui/project_path.py`; `launcher.py` exports `show_assistant_shell` only
2. **Shell integration tests** — CLI deep links, context propagation, tab badges, last-tab restore
3. **Conversation persistence** — disk-backed `SessionStore` + `get_session_store()` singleton
4. **Enhanced Chat UX** — markdown display formatting, token/cost per assistant turn, template hint
5. **Plugin verification** — `tests/plugin/test_macos_plugin_path.py` (Documents/KiCad/10.0 path)
6. **Docs** — ADP-011 Phase D complete, testing guide, MASTER_TASK_LIST updated

ENTRY POINTS
------------
- Terminal: `python scripts/run_ai_assistant.py /path/to/project.kicad_pro --ui`
- Deep links: `--ui-chat`, `--ui-datasheets`, `--ui-simulation`, `--ui-aerf`, `--ui-notebook`
- KiCad: Tools → External Plugins → KiCad AI Assistant
- macOS plugin symlink: `~/Documents/KiCad/10.0/scripting/plugins/kicad_ai_assistant.py`
  → repo `src/plugin/kicad_ai_assistant_plugin.py`

RECOMMENDED NEXT
----------------
- Incremental context refresh between chat turns (reduce API cost)
- Multi-provider settings UI (OpenAI / Ollama)
- True wxAUI docking inside KiCad editor (deferred)

PRIOR — Phase 2 Sprint 3 (ADP-011 Phase C)
------------------------------------------
KiCad ActionPlugin, Conversation Manager (in-memory), multi-turn Chat, shell polish.

AUTHORITATIVE STATUS
--------------------
- `tasks/MASTER_TASK_LIST.md` (Last Reviewed: 2026-08-23)
- `docs/Architecture/ADP-011-Assistant-Shell-UI.md`
```
