# Minimal Blocking Oscillator Example

Small bundled KiCad project for smoke tests and AERF validation without a full Bedini SSG clone.

## Contents

- `Q1` — NPN switching transistor (`Device:Q_NPN_BCE`)
- `T1` — custom trifilar coil symbol (`Device:T_Custom`)
- `R1` — base bias resistor with custom field `Vds_max`
- Net labels: `COIL_PLUS`, `TRIGGER`, `FEEDBACK`

The classifier should recognize this as **blocking_oscillator** (Q + T symbols + coil/trigger net keywords).

## Run

```bash
python scripts/run_ai_assistant.py examples/minimal_blocking_oscillator/blocking_oscillator.kicad_pro --ui-aerf
python scripts/run_ai_assistant.py examples/minimal_blocking_oscillator/blocking_oscillator.kicad_pro --ui-chat
```

## Sample questions

- Summarize the blocking oscillator topology and key components.
- Which pins appear unconnected in the extracted context?
- What circuit family does the classifier select?

## Related

- Full Bedini live validation: [AERF Validation Rubric](../../docs/User_Guides/AERF_Validation_Rubric.md)
- Reference workflow placeholder: [bedini_babcock/README.md](../bedini_babcock/README.md)
