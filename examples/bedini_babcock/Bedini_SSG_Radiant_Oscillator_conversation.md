# KiCad AI — Bedini_SSG_Radiant_Oscillator

_Project: `Bedini_SSG_Radiant_Oscillator/Bedini_SSG_Radiant_Oscillator.kicad_pro` (sample export from Chat → Expand… → Save as markdown…)_

---

## You

_2026-09-18T09:35:36.990661+00:00_

Analyze the flyback energy-recovery paths associated with Q1/D1/ChargeBT2 and Q2/D2/ChargeBT1. Explain what happens when each transistor switches OFF, trace the expected inductive current path, and determine whether D1 and D2 are correctly oriented to recover flyback energy into the corresponding 6 V charging batteries. Identify any problems with the topology, diode selection, or component ratings, and recommend specific improvements. Also identify any conditions that could produce excessive voltage across Q1 or Q2.

---

## Assistant

_2026-09-18T09:35:36.990718+00:00_

# Flyback Energy-Recovery Path Audit: Bedini SSG Radiant Oscillator

---

## 1. Netlist Topology Reconstruction

Before analyzing switching behavior, I must establish the actual connectivity from the netlist, since **all T1 pins and both transistors show as unconnected in the schematic pin-connectivity table** — a critical data quality problem addressed in Section 7.

From the SPICE netlist preview lines, the following connections can be reconstructed:

```
XT1 Net-_ChargeBT1--_  Net-_D1-A_  Net-_T1-T1_  Net-_PrimaryBT1--_  Net-_ChargeBT1--_  Net-_D2-A_  BEDINI_TRIFILAR
XQ1  Net-_D1-A_   Net-_Q1-B_   Net-_PrimaryBT1--_   BD243C
XQ2  Net-_D2-A_   Net-_Q2-B_   Net-_PrimaryBT1--_   BD243C
D1   Net-_D1-A_   Net-_ChargeBT2-+_   __D1
D2   Net-_D2-A_   Net-_ChargeBT1-+_   __D2
VPrimaryBT1  Net-_ChargeBT1--_  Net-_PrimaryBT1--_   DC 6
VChargeBT1   Net-_ChargeBT1-+_  Net-_ChargeBT1--_   DC 6
VChargeBT2   Net-_ChargeBT2-+_  Net-_ChargeBT1--_   DC 6
```

### Reconstructed Net Map

| Net Name | Function | Connected To |
| --- | --- | --- |
| `Net-_PrimaryBT1--_` | Circuit GND / emitter rail | Q1-E, Q2-E, R1-pin2, R4-pin2 |
| `Net-_ChargeBT1--_` | T1 supply side / negative charge rail | T1-pin1, T1-pin5, PrimaryBT1+ |
| `Net-_D1-A_` | Q1 collector / T1 output winding 1 | Q1-C, T1-pin2, D1-A, R2-pin1, R5-pin1† |
| `Net-_D2-A_` | Q2 collector / T1 output winding 2 | Q2-C, T1-pin6, D2-A, R5-pin1 |
| `Net-_Q1-B_` | Q1 base drive | R1-pin1, R2-pin2, R3-pin2 |
| `Net-_Q2-B_` | Q2 base drive | R4-pin1, R5-pin2, R6-pin2 |
| `Net-_R3-Pad1_` | Trigger winding junction | R3-pin1, R6-pin1, T1-pin3 (via R7) |
| `Net-_ChargeBT1-+_` | ChargeBT1 positive terminal | D2-K |
| `Net-_ChargeBT2-+_` | ChargeBT2 positive terminal | D1-K |
| `Net-_T1-T1_` | Trigger winding tap | T1-pin4(?), R7 wiper |

> †R5 connectivity ambiguity is flagged in Section 6.

---

## 2. Transistor Switch-OFF Flyback Trace: Q1 Path

### Coil Winding Assignment (from BEDINI_TRIFILAR subcircuit pin order)

Based on the netlist `XT1` pin ordering and standard Bedini trifilar convention:

| T1 Pin | Net | Role |
| --- | --- | --- |
| Pin 1 | `Net-_ChargeBT1--_` | Drive winding (+), supply side |
| Pin 2 | `Net-_D1-A_` | Drive winding (−), Q1 collector side |
| Pin 3 | `Net-_T1-T1_` | Trigger winding terminal |
| Pin 4 | `Net-_PrimaryBT1--_` | Trigger winding return |
| Pin 5 | `Net-_ChargeBT1--_` | Recovery winding (+) |
| Pin 6 | `Net-_D2-A_` | Recovery winding (−), Q2 collector side |

### Q1 ON-State Current Path

```
PrimaryBT1(+6V) → Net-_ChargeBT1--_ → T1 Pin1
  → [Drive winding, building magnetic flux]
  → T1 Pin2 (Net-_D1-A_)
  → Q1 Collector → Q1 Emitter
  → Net-_PrimaryBT1--_ → PrimaryBT1(−)
```

During this phase, energy is stored in T1's magnetic core.

### Q1 Switch-OFF: Flyback Event

When Q1's base drive is removed:

1. **Collector current collapses** abruptly.
2. The drive winding (Pins 1–2) generates a **flyback EMF** that opposes the current collapse: `V_flyback = -L × dI/dt`. The polarity **reverses** relative to the ON-state.
3. `Net-_D1-A_` (T1 Pin 2) swings **positive** relative to `Net-_ChargeBT1--_` (T1 Pin 1).
4. The inductive energy seeks a discharge path.

### Expected Flyback Recovery Path Through D1

```
T1 Pin2 (Net-_D1-A_) [now HIGH, flyback polarity]
  → D1 Anode (Net-_D1-A_)
  → D1 Cathode → Net-_ChargeBT2-+_
  → ChargeBT2 (6V) positive terminal → [charging current flows]
  → ChargeBT2 negative terminal → Net-_ChargeBT1--_
  → T1 Pin1 [flyback current loop closes]
```

**D1 orientation assessment:** D1's anode is on `Net-_D1-A_` and cathode on `Net-_ChargeBT2-+_`. When `Net-_D1-A_` goes positive during flyback, D1 **conducts correctly** — this orientation is **electrically sound** for flyback recovery.

---

## 3. Transistor Switch-OFF Flyback Trace: Q2 Path

### Q2 ON-State Current Path

```
PrimaryBT1(+6V) → Net-_ChargeBT1--_ → T1 Pin5
  → [Recovery winding, building flux]
  → T1 Pin6 (Net-_D2-A_)
  → Q2 Collector → Q2 Emitter
  → Net-_PrimaryBT1--_ → PrimaryBT1(−)
```

### Q2 Switch-OFF: Flyback Event

1. `Net-_D2-A_` (T1 Pin 6) swings **positive** during flyback.
2. D2 anode is on `Net-_D2-A_`, cathode on `Net-_ChargeBT1-+_`.

### Expected Flyback Recovery Path Through D2

```
T1 Pin6 (Net-_D2-A_) [now HIGH, flyback polarity]
  → D2 Anode (Net-_D2-A_)
  → D2 Cathode → Net-_ChargeBT1-+_
  → ChargeBT1 (6V) positive terminal → [charging current flows]
  → ChargeBT1 negative terminal (Net-_ChargeBT1--_)
  → T1 Pin5 [flyback current loop closes]
```

**D2 orientation assessment:** D2's anode is on `Net-_D2-A_` and cathode on `Net-_ChargeBT1-+_`. When `Net-_D2-A_` goes positive during flyback, D2 **conducts correctly** — orientation is **electrically sound**.

---

## 4. Critical Problems Identified

### Problem 1 — FATAL: Ground Rail Ambiguity and Floating Reference ⚠️

**The most severe issue in this design.**

From the netlist:
```
VPrimaryBT1  Net-_ChargeBT1--_  Net-_PrimaryBT1--_   DC 6
```

This means:
- `Net-_ChargeBT1--_` is the **positive terminal** of PrimaryBT1 (= +6V supply rail, feeding T1 coil)
- `Net-_PrimaryBT1--_` is the **negative terminal** (= circuit GND, Q1/Q2 emitters)

**However**, the net name `Net-_PrimaryBT1--_` appears on R1-pin2 and R4-pin2, which feed the base bias resistor dividers. This means the base bias networks (R1, R2, R4, R5) **reference the emitter ground correctly** — but the naming is deeply confusing.

More critically:
```
VChargeBT1   Net-_ChargeBT1-+_  Net-_ChargeBT1--_   DC 6
VChargeBT2   Net-_ChargeBT2-+_  Net-_ChargeBT1--_   DC 6
```

Both ChargeBT1 and ChargeBT2 have their **negative terminals tied to `Net-_ChargeBT1--_`** — the **+6V supply rail**, not circuit GND. This means:
- ChargeBT1(+) = `Net-_ChargeBT1-+_` = 6V above the coil supply rail = **+12V above GND**
- ChargeBT2(+) = `Net-_ChargeBT2-+_` = also **+12V above GND**

**Consequence:** The charging batteries float above the primary supply. The flyback diodes D1 and D2 must block 12V in reverse (ChargeBT voltage + primary voltage) during the transistor ON states. The 1N4007's 1000V PRV is adequate, but the **charge battery grounds are not connected to circuit GND**, creating a floating topology. In hardware, if ChargeBT− is connected to a common chassis ground, the circuit will short.

**Recommendation:** Add explicit net labels distinguishing `PWR_GND` (emitter/PrimaryBT1−), `COIL_PLUS` (PrimaryBT1+/coil supply), and `CHRG_GND`. Connect ChargeBT− terminals to `PWR_GND`, not `COIL_PLUS`, unless the isolated floating topology is intentional and fully documented.

---

### Problem 2 — CRITICAL: R5 Cross-Coupling Creates Feedback Short

From the netlist:
```
R5 Net-_D2-A_ Net-_Q2-B_ 18k
```

And from the schematic connectivity:
```
R5 pin1 → Net-_D2-A_   (Q2 collector / D2 anode — flyback node)
R5 pin2 → Net-_Q2-B_   (Q2 base)
```

R5 (18K) connects Q2's **collector (flyback node `Net-_D2-A_`)** directly back to **Q2's base** (`Net-_Q2-B_`).

**This is a collector-to-base feedback resistor on Q2.** During the flyback transient when `Net-_D2-A_` swings to high voltage (potentially 50–200V above rail in a Bedini circuit), R5 will **drive Q2's base positive**, attempting to turn Q2 back ON during the flyback interval.

This creates:
- **Parasitic re-triggering** of Q2 during the flyback pulse
- **Partial clamping** of the flyback voltage at approximately `V_be(on) × (1 + R4/R5)` ≈ `0.7 × (1 + 10K/18K)` ≈ **1.1V above rail** — completely suppressing the flyback pulse before D2 can route it to ChargeBT1
- Potential **Q2 secondary breakdown** if the collector swings high while simultaneously driving base current

Compare to R2 (18K) which mirrors this for Q1:
```
R2  Net-_D1-A_  Net-_Q1-B_  18k
```
R2 creates the identical problem on the Q1/D1 path.

**In a standard Bedini SSG, R2/R5 are the "trigger resistors" connecting the feedback winding to the base — but they should connect from the TRIGGER WINDING output, not from the collector node.** The current netlist conflates the collector node with the trigger winding tap.

**Recommendation:** Route R2-pin1 and R5-pin1 from the trigger winding terminal (`Net-_T1-T1_` or equivalent) rather than from `Net-_D1-A_` / `Net-_D2-A_`. This is the defining feature of the Bedini SSG topology — trigger feedback must come from a **magnetically isolated feedback winding**, not the power collector.

---

### Problem 3 — SEVERE: T1 Trigger Winding Path Is Broken

From the netlist:
```
AR7  Net-_T1-T1_  Net-_T1-T1_  Net-_R3-Pad1_  __R7
```

R7 (1K potentiometer) has:
- Pin 1 → `Net-_T1-T1_`
- Pin 2 → `Net-_T1-T1_` (wiper tied to the same terminal — **no voltage division occurs**)
- Pin 3 → `Net-_R3-Pad1_`

The potentiometer is wired with both end-terminals shorted together on `Net-_T1-T1_`, making R7 a **fixed resistor from T1-trigger to R3-pad1**, not an adjustable speed control. The wiper (pin 2) provides no adjustment function.

Furthermore, `Net-_R3-Pad1_` connects to R3-pin1 and R6-pin1:
```
R3  Net-_R3-Pad1_  Net-_Q1-B_  560r   → Q1 base series resistor
R6  Net-_R3-Pad1_  Net-_Q2-B_  560r   → Q2 base series resistor
```

So the trigger winding drives both Q1 and Q2 bases simultaneously through a common node — **there is no differential oscillation mechanism**. Both transistors will switch ON and OFF together, preventing the intended alternating push-pull or sequential firing of a multi-strand SSG.

**Recommendation:** Separate the trigger paths: Trigger Winding A → R3 → Q1 base; Trigger Winding B (opposing polarity) → R6 → Q2 base. This requires the trigger winding to have a center tap or use two opposing-wound trigger strands, each connected to only one transistor's base.

---

### Problem 4 — SEVERE: All T1 Pins and Transistor Pins Show Unconnected in Schematic

The schematic pin-connectivity table reports **21 unconnected pins out of 37 total**, including:
- All 6 pins of T1
- All 3 pins of Q1 (collector, base, emitter)
- All 3 pins of Q2
- Both pins of ChargeBT1, ChargeBT2, PrimaryBT1

The SPICE netlist **does** show connectivity (extracted from wire routing), but the KiCad schematic symbol pins are **not electrically connected via wires or net labels** in the schematic editor. This means:

1. **ERC will flag these as errors** when enabled
2. **PCB netlist export will produce an empty board** (confirmed: PCB shows 0 footprints, 0 nets, 0 tracks)
3. The schematic is **non-manufacturable** in current state

---

### Problem 5 — MODERATE: BD243C in TO-92 Footprint — Rating Mismatch

The BD243C is a **TO-220 package** rated at:
- I_C(max) = 6A
- V_CEO =

*7972 in / 4096 out tokens · claude-sonnet-4-6 · ~$0.0854*
