# Bedini / Babcock Reference Example

Validation scenario for flyback recovery and patent-driver PCB analysis — not the full project scope.

## Flyback recovery audit template

Use the **Flyback recovery** audit in the **Audits** tab or the **Flyback recovery** Chat template to review:

- Optocoupler / GPIO isolation from HV switching loops
- Flyback diode and transistor stress
- Net labels such as `HV_Flyback`, `Coil_Plus`, `PICO_GPIO15` when present
- Netlist vs schematic consistency

Design intent and firmware stub for manual validation:

- [design_intent.md](design_intent.md) — switching frequency, voltage targets, isolation requirements
- [firmware/pico_gpio_stub/](firmware/pico_gpio_stub/) — Pico GPIO timing reference for cross-review and future Level 1 DCBM validation ([ADP-014](../../docs/Architecture/ADP-014-Firmware-Aware-Mixed-Domain-Simulation.md))

Labeled nets for smoke tests live in [minimal_blocking_oscillator](../minimal_blocking_oscillator/blocking_oscillator.kicad_sch) (`HV_Flyback`, `Coil_Plus`, `PICO_GPIO15`, etc.).

## Bundled smoke-test project

For CI and local smoke tests without a full Bedini SSG schematic, use:

**[minimal_blocking_oscillator](../minimal_blocking_oscillator/README.md)** — small blocking-oscillator KiCad project with transistor, coil, and labeled nets.

## Full Bedini validation

Live AERF stages 0–7 sign-off uses captured fixtures in `tests/fixtures/bedini_aerf_live/` and the [AERF Validation Rubric](../../docs/User_Guides/AERF_Validation_Rubric.md). Run against your own Bedini project when available.

## Sample questions

- Summarize the active silicon parts and their datasheet coverage.
- Which nets look like high-voltage or flyback recapture paths?
- Are there missing required datasheets blocking SUBCKT analysis?

## Run

With the minimal example:

```bash
python scripts/run_ai_assistant.py examples/minimal_blocking_oscillator/blocking_oscillator.kicad_pro --ui-chat
```

With the built-in test fixture:

```bash
python scripts/run_ai_assistant.py tests/fixtures/testproj.kicad_pro
```

See [Testing With Your KiCad Project](../../docs/User_Guides/Testing_With_Your_KiCad_Project.md), [E2E Chat UI validation](../../docs/Developer_Handbook/06_E2E_Chat_UI.md), and [E2E Full Flow](../../docs/Developer_Handbook/07_E2E_Full_Flow.md).
