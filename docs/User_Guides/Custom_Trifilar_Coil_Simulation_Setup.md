# Custom Trifilar Coil — KiCad Simulation Setup

Step-by-step reference for setting up a **custom wound inductor** (e.g. Bedini SSG trifilar air-core coil **T1**) for SPICE simulation in KiCad.

This applies to components that have **no catalog simulation model**. Unlike parts such as `1N4007` (built-in `Sim.Device=D`), a custom coil needs:

1. A **symbol** with numbered pins and design-parameter fields  
2. A **SUBCKT `.lib` file** with electrical values (L, R, coupling)  
3. **KiCad SUBCKT hookup** on the symbol (`Sim.Device=SUBCKT`, etc.)

A future AI “custom component builder” may automate this; for now the workflow is manual (or AI-assisted for `.lib` generation), following the same pattern as datasheet-backed SUBCKT parts (e.g. BD243C).

---

## Overview

| Layer | Where it lives | Purpose |
|-------|----------------|---------|
| **Design** | Custom properties on T1 | Turns, wire gauge, coil geometry — what you optimize |
| **Electrical model** | `Bedini_Trifilar.lib` | L, R, k — what ngspice simulates |
| **KiCad binding** | `Sim.Device=SUBCKT`, etc. | Connects schematic pins to the SUBCKT |

**Important:** Custom symbol fields (inches, turn counts) are **metadata only**. KiCad does not pass them to ngspice automatically. Something (you or the AI assistant) must convert geometry → L/R/k when building the `.lib` file.

---

## Example design parameters (Bedini T1)

These are typical starting values; adjust to your build.

| Property | Example value | Meaning |
|----------|---------------|---------|
| `N_Primary` | `450` | Primary turn count |
| `N_Trigger` | `50` | Trigger / feedback turns |
| `N_Secondary` | `450` | Secondary turns |
| `Wire_Gauge` | `22 AWG` | Wire size → resistance |
| `Coil_ID` | `6 in` | Inner diameter (bobbin ID) |
| `Coil_OD` | `7 in` | Outer diameter after winding |
| `Coil_Width` | `1 in` | Winding length along bobbin axis |
| `Coil_Depth` | `0.5 in` | Radial build; should match `(OD − ID) / 2` |
| `Coupling_k` | `0.98` | Mutual coupling (trifilar on same bobbin) |

**Units:** Inches on the symbol are fine. KiCad stores them as text. Convert to metres (or mm) only when computing L/R for the `.lib` file (e.g. `6 in = 0.1524 m`).

Optional: add `Coil_Units` = `in` so tools and future AI passes know the convention.

---

## Step 1 — Fix the symbol (pins and reference)

The library symbol must have **numbered, named pins** before simulation works. An unnumbered symbol cannot map `Sim.Pins` to the SUBCKT.

### 1.1 Open Symbol Editor

1. KiCad main window → **Symbol Editor** (not Schematic Editor).
2. Load library **Custom_Inductors** (path is in project `sym-lib-table`, e.g. `Custom_Inductors.kicad_sym`).
3. Open **Bedini_Coil_1**.

### 1.2 Assign pin numbers and names

Edit each of the six pins (map to your schematic wiring):

| Pin # | Name | Typical role |
|-------|------|----------------|
| 1 | `P1` | Primary start |
| 2 | `P2` | Primary end |
| 3 | `T1` | Trigger start |
| 4 | `T2` | Trigger end |
| 5 | `S1` | Secondary start |
| 6 | `S2` | Secondary end |

Pin positions on the default symbol (for orientation):

- Left pair: pins 1–2 (primary)  
- Middle pair: pins 3–4 (trigger)  
- Right pair: pins 5–6 (secondary)

**Verify wiring:** Primary to transistor/collector path, trigger to base, secondary to charge path. Swap names if your physical winding order differs — SUBCKT port order must match the schematic.

### 1.3 Change default reference prefix L → T

1. Select the **Reference** property on the symbol (or root symbol in the tree).
2. Change value from **`L`** to **`T`**.
3. New placements get `T1`, `T2`, … instead of `L1`, `L2`.

Existing instances (e.g. **T1** already on the schematic) keep their reference; only new placements use the default.

### 1.4 Save

**File → Save** the symbol library.

### 1.5 Refresh schematic instance

- If KiCad prompts to update the symbol from the library, accept.
- On the schematic: enable **Show pin numbers** on T1 if helpful while wiring.
- Confirm **Exclude from simulation** is **unchecked**.

---

## Step 2 — Add design-parameter fields on T1

1. Schematic → select **T1** → **Properties** (or `E`).
2. Use **Add property** for each design field (see table above).
3. Set **Value** to something readable (e.g. `Bedini Trifilar`); geometry stays in named fields.
4. Save the schematic.

These fields are your **design record** for analysis and future AI optimization. They do not enable simulation by themselves.

---

## Step 3 — Create the SUBCKT library file

KiCad cannot simulate T1 until a `.lib` exists with a `.SUBCKT` definition.

### 3.1 Choose file location

Mirror the BD243C layout in your project:

```
<project>/kicad_ai/subckt/Bedini_Trifilar/
```

Shared library path (example):

```
~/Development/Local/kicad_ai_library/libs/Bedini_Trifilar.lib
```

Use a **stable path**; `Sim.Library` and `Spice_Lib` will point here.

### 3.2 Starter SUBCKT (fixed L/R/k — tune later)

Create `Bedini_Trifilar.lib`:

```spice
* Bedini SSG — trifilar air-core coil (STARTER MODEL — tune L/R/k)
* Ports: P1 P2 = primary, T1 T2 = trigger, S1 S2 = secondary
.SUBCKT BEDINI_TRIFILAR P1 P2 T1 T2 S1 S2

* Primary (example values — replace after geometry calc)
Lp P1 P2 3m Rser=1.5

* Trigger (fewer turns → smaller L)
Lt T1 T2 30u Rser=0.15

* Secondary
Ls S1 S2 3m Rser=1.5

* Mutual coupling (tightly twisted trifilar on same bobbin)
Kpt Lp Lt 0.98
Kps Lp Ls 0.98
Kts Lt Ls 0.98

.ENDS BEDINI_TRIFILAR
```

### 3.3 Smoke-test syntax

```bash
ngspice -b -o /dev/null /path/to/Bedini_Trifilar.lib
```

No errors means the file parses.

### 3.4 Starter electrical ranges (ballpark)

| Winding | Turns (example) | L (starter) | R (starter) |
|---------|-------------------|-------------|-------------|
| Primary | 400–600 | 1–10 mH | 0.5–3 Ω |
| Trigger | 30–80 | 10–100 µH | 0.05–0.5 Ω |
| Secondary | 400–600 | 1–10 mH | 0.5–3 Ω |
| Coupling k | — | 0.95–0.99 | — |

Refine L/R from `N_*`, `Wire_Gauge`, and `Coil_ID` / `Coil_OD` / `Coil_Width` when you or the AI assistant compute inductance (e.g. Wheeler-style formulas on mean diameter).

### 3.5 Optional documentation alongside the lib

Create `kicad_ai/subckt/Bedini_Trifilar/assumptions.md` noting formulas, unit conversions, and chosen L/R/k — same pattern as `kicad_ai/subckt/BD243C/`.

---

## Step 4 — Hook T1 to the SUBCKT in KiCad

### Option A — Simulation Model editor (recommended first time)

1. Select **T1** → **Properties** → **Simulation Model…**
2. Set:
   - **Device type:** SUBCKT (subcircuit)
   - **Model source:** from file
   - **File:** full path to `Bedini_Trifilar.lib`
   - **Model name:** `BEDINI_TRIFILAR`
3. **Pin assignments:**

   ```
   1=P1  2=P2  3=T1  4=T2  5=S1  6=S2
   ```

4. OK → save schematic.

### Option B — KiCad AI Assistant Simulation panel

After the `.lib` is registered in the artifact catalog for the part value:

1. **Refresh context** on the project.
2. **Simulation** panel → select T1 row → **Apply simulation model…**

For a new custom part, Option A is usually faster until SUBCKT is generated or registered via the assistant.

### Expected symbol fields after hookup

```
Sim.Device       = SUBCKT
Sim.Library      = .../Bedini_Trifilar.lib
Sim.Name         = BEDINI_TRIFILAR
Sim.Pins         = 1=P1 2=P2 3=T1 4=T2 5=S1 6=S2
Spice_Model      = BEDINI_TRIFILAR
Spice_Primitive  = X
Spice_Lib        = .../Bedini_Trifilar.lib
```

If the schematic was open in KiCad during an external write: **File → Revert** on that sheet to reload properties from disk.

---

## Step 5 — Verify netlist export

```bash
kicad-cli sch export netlist --format spice \
  -o /tmp/bedini.net \
  /path/to/Bedini_SSG_Radiant_Oscillator.kicad_sch
```

Check:

- T1 appears as an `X` instance for `BEDINI_TRIFILAR`
- Netlist includes `.include` (or equivalent) for `Bedini_Trifilar.lib`
- No `No simulation model definition found` for **T1**

In **KiCad AI Assistant**: **Refresh context** → **Simulation** panel — T1 should leave the missing-models list when hookup is complete.

Remaining netlist errors may be other parts (e.g. SUBCKT path for BD243C), not standard passives or diodes.

---

## Step 6 — First simulation run

1. KiCad **Simulator** → run transient analysis.
2. Observe: Q1 switching, collector voltage, secondary behaviour.
3. If no oscillation: adjust **Lt** (trigger) and **Lp** first — most sensitive for a blocking oscillator.

Document trials in `assumptions.md` or the project Engineering Notebook.

---

## Step 7 — Iterate (manual and AI-assisted)

### Manual loop

1. Change geometry / turn fields on T1.  
2. Recompute or hand-edit L/R in `.lib`.  
3. Re-export netlist → re-simulate.

### AI-assisted loop (project direction)

1. Use **Chat** or **AERF** with T1 properties: ask for Lp, Lt, Ls, R, k from N, AWG, Coil_ID, Coil_OD, Coil_Width.  
2. Update `Bedini_Trifilar.lib` and `assumptions.md`.  
3. Re-apply simulation model if needed → re-simulate.

---

## Checklist

- [ ] Symbol pins numbered 1–6 with names P1/P2/T1/T2/S1/S2  
- [ ] Default reference prefix **T** in library  
- [ ] T1 wiring matches pin roles  
- [ ] Design fields on T1 (N_*, Wire_Gauge, Coil_*, Coupling_k)  
- [ ] `Bedini_Trifilar.lib` created and ngspice syntax-checked  
- [ ] T1 `Sim.Device=SUBCKT` with correct library, name, and pins  
- [ ] Netlist exports without T1 errors  
- [ ] First transient simulation run  

---

## Related docs

- [Testing With Your KiCad Project](./Testing_With_Your_KiCad_Project.md)  
- [Feature Overview](./Feature_Overview.md) — Simulation / SUBCKT gap-fill  
- [Netlist Gap Fill](../Specifications/Netlist_Gap_Fill.md)  
- Blocking Oscillator knowledge: `docs/Engineering_Knowledge/Circuit_Families/Blocking_Oscillator/`  

---

## Why not built-in `Sim.Device=L`?

A single inductor value cannot represent three coupled windings. ngspice needs:

- Three inductors (or equivalent)  
- Mutual coupling (`K`) between windings  
- Series resistance per winding  

That structure lives in a **SUBCKT**, not in KiCad’s built-in passive auto-models.

---

*Last updated for Bedini SSG Radiant Oscillator — Custom_Inductors:Bedini_Coil_1 / T1.*
