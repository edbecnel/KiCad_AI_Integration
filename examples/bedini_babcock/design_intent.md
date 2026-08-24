# Bedini / Babcock — Design Intent

Reference design intent for manual validation of flyback recovery audits and cross-domain checks (schematic, PCB, firmware).

## Switching and power targets

| Parameter | Target | Notes |
|-----------|--------|-------|
| Switching frequency | 20–80 kHz (example) | Blocking oscillator / SSG validation range |
| Primary rail | 12 V DC input (example) | Low-voltage bias for control stage |
| HV flyback recapture | 100–400 V peak (example) | Lab measurement only — not a product spec |
| Isolation | Galvanic isolation between Pico GPIO and HV switching loop | Optocoupler or level-shift required |

## Labeled nets (validation)

When a full Bedini SSG schematic is unavailable, the bundled [minimal_blocking_oscillator](../minimal_blocking_oscillator/README.md) uses these labels for smoke tests:

| Net label | Role |
|-----------|------|
| `COIL_PLUS` / `Coil_Plus` | Primary coil / flyback recapture path |
| `HV_Flyback` | High-voltage switching or recapture node (alias in docs) |
| `PICO_GPIO15` | Low-voltage control GPIO (firmware stub reference) |
| `TRIGGER` | Oscillator trigger / bias |
| `FEEDBACK` | Regenerative feedback path |

## Isolation requirements

1. Control MCU (Pico) GPIO must not share a galvanic path with HV switching nodes.
2. Flyback diode and switching transistor stress must be reviewed against expected Vds spikes.
3. Creepage/clearance on PCB must be validated for HV sections when a board exists.

## Firmware cross-review

See [firmware/pico_gpio_stub/README.md](firmware/pico_gpio_stub/README.md) for timing constants used in GPIO isolation and dead-time checks against the netlist.

## Related

- [README.md](README.md)
- [Manual Validation Checklist](../../docs/Developer_Handbook/Manual_Validation_Checklist.md)
