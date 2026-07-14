# Bedini / Babcock Reference Example (placeholder)

Validation scenario for flyback recovery and patent-driver PCB analysis — not the full project scope.

## Sample questions

- Summarize the active silicon parts and their datasheet coverage.
- Which nets look like high-voltage or flyback recapture paths?
- Are there missing required datasheets blocking SUBCKT analysis?

## Run

```bash
python scripts/run_ai_assistant.py "/path/to/Babcock-Patent-Driver-PCB-4p.kicad_pro" --ui-chat
```

See [E2E Chat UI validation](../docs/Developer_Handbook/06_E2E_Chat_UI.md).
