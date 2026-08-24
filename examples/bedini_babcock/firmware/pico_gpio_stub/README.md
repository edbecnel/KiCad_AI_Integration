# Pico GPIO stub — Bedini validation

Minimal firmware stub for cross-review with schematic net labels (`PICO_GPIO15`, isolation timing).

## Purpose

Not runnable production firmware — documents expected GPIO timing and isolation assumptions for AI-assisted review:

- GPIO15 drives optocoupler LED (low-voltage side)
- Minimum dead-time between PWM edges: **2 µs** (example)
- Maximum GPIO toggle rate: **50 kHz** (example)

## Constants (reference)

```c
#define PICO_GPIO_PIN       15
#define DEAD_TIME_US        2
#define MAX_PWM_HZ          50000
```

## Sample review questions

- Does the netlist show `PICO_GPIO15` isolated from `HV_Flyback` / `Coil_Plus`?
- Is optocoupler propagation delay accounted for in dead-time?
- Are flyback diode and transistor ratings consistent with design intent?

## Related

- [design_intent.md](../../design_intent.md)
- [bedini_babcock README](../../README.md)
