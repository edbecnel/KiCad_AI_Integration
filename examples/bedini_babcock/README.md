# Bedini / Babcock Reference Example (placeholder)

Validation scenario for flyback recovery and patent-driver PCB analysis — not the full project scope.

A bundled sample project is not yet included in this directory. Use your own KiCad project or the repository fixture `tests/fixtures/testproj.kicad_pro` for smoke testing.

**Full testing guide:** [Testing With Your KiCad Project](../docs/User_Guides/Testing_With_Your_KiCad_Project.md)

## Sample questions

- Summarize the active silicon parts and their datasheet coverage.
- Which nets look like high-voltage or flyback recapture paths?
- Are there missing required datasheets blocking SUBCKT analysis?

## Run

With your own project:

```bash
python scripts/run_ai_assistant.py "/path/to/your/project.kicad_pro" --ui-chat
```

With the built-in fixture (no API key needed for context-only):

```bash
python scripts/run_ai_assistant.py tests/fixtures/testproj.kicad_pro
```

See [E2E Chat UI validation](../docs/Developer_Handbook/06_E2E_Chat_UI.md) and [E2E Full Flow](../docs/Developer_Handbook/07_E2E_Full_Flow.md).
