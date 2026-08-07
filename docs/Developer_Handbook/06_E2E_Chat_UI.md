# E2E Validation — Chat UI and Prompt Builder

[Home](../../README.md) · [Project Index](../../PROJECT_INDEX.md) · [Developer Handbook](README.md)

> **Status:** Maintained
> **Owner:** Project maintainers
> **Applies To:** Manual validation of Phase 1 Tier 1 slices
> **Last Reviewed:** 2026-08-07
> **Review Frequency:** Quarterly

## Prerequisites

- `~/kicad_ai_config.json` with `anthropic_api_key`, `ai_provider: "claude"`, `claude_model`
- Test project with saved schematic (e.g. Babcock patent driver)
- wxPython: `pip install wxPython` (for Terminal UI on macOS)

## Terminal launch (recommended on macOS)

KiCad Scripting Console paste/focus may be broken — use Terminal:

```bash
python /path/to/KiCad_AI_Integration/scripts/run_ai_assistant.py \
  "/path/to/project.kicad_pro" \
  --ui-chat
```

Missing datasheets panel:

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui-datasheets
```

Dev smoke (no Approve & Send):

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" \
  --ask "Summarize active parts" --image
```

## Chat UI checklist

1. Dialog opens; API key field pre-filled from config (masked).
2. **Refresh context** populates preview (project name, symbol count, datasheet stats).
3. Optional **Include schematic image** updates preview byte-size line when export succeeds.
4. Enter a question; preview shows prompt excerpt and estimated tokens.
5. **Approve & Send** shows confirmation dialog — **Cancel** must not call Anthropic.
6. **Approve** sends request; response appears in read-only area with token counts.
7. **Close** returns shell prompt (external Terminal).

## Security checklist

- [ ] No API transmission before Approve & Send confirmation (`--ui-chat`)
- [ ] Context preview visible before send
- [ ] `--ask` documented as dev-only bypass

## Automated tests

```bash
pytest tests/prompts/ tests/ui/test_chat_supply.py -q
```

Golden prompt excerpt: `tests/prompts/golden/general_review_prompt.txt`

## Parent

- [Developer Handbook](README.md)
