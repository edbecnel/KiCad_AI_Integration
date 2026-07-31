# Custom Trifilar Coil — KiCad Simulation Setup

Step-by-step reference for setting up a **custom wound inductor** (e.g. Bedini SSG trifilar air-core coil **T1**) for SPICE simulation in KiCad.

This applies to components that have **no catalog simulation model**. Unlike parts such as `1N4007` (built-in `Sim.Device=D`), a custom coil needs:

1. A **symbol** with numbered pins and design-parameter fields  
2. A **SUBCKT `.lib` file** with electrical values (L, R, coupling)  
3. **KiCad SUBCKT hookup** on the symbol (`Sim.Device=SUBCKT`, etc.)

A future AI “custom component builder” may automate geometry → `.lib` generation; for now the workflow is manual or AI-assisted, following the same pattern as datasheet-backed SUBCKT parts (e.g. BD243C).

---

## Overview — three layers

| Layer | Where it lives | Purpose |
|-------|----------------|---------|
| **Design** | Custom properties on T1 | Turns, wire gauge, coil geometry — what you optimize |
| **Electrical model** | `Bedini_Trifilar.lib` | L, R, k — what ngspice simulates |
| **KiCad binding** | `Sim.Device=SUBCKT`, etc. | Connects schematic pins to the SUBCKT |

**Important:** Custom symbol fields (inches, turn counts) are **metadata only**. KiCad does not pass them to ngspice automatically. You (or the AI assistant) must convert geometry → L/R/k when building or updating the `.lib` file.

---

## Two kinds of symbol properties (don’t mix them up)

KiCad shows all properties in one list, but they serve different roles.

### Design / documentation fields (Step 2)

These record **what you are building**. They do not enable simulation.

| Property | Example | Notes |
|----------|---------|--------|
| `Value` | `Multi-Strand SSG` | Short part label (BOM, Simulation panel grouping) |
| `N_Primary` / `N_Trigger` / `N_Secondary` | `450` / `50` / `450` | Turn counts |
| `Wire_Gauge` | `22 AWG` | |
| `Coil_ID` | `6 in` | Inner bobbin diameter |
| `Coil_OD` | `7 in` | Outer diameter; `Coil_Depth` ≈ `(OD − ID) / 2` |
| `Coil_Width` | `1 in` | Winding length along bobbin |
| `Coil_Depth` | `0.5 in` | Radial build |
| `Coupling_k` | `0.98` | Starting mutual coupling estimate |
| `Coil_Units` | `in` | Optional — documents unit convention |

**Inches are fine** on the symbol. KiCad stores them as text. Convert to metres/mm only when computing L/R for the `.lib` (e.g. `6 in = 0.1524 m`).

**`Value` vs custom fields:** Put a readable part name in **Value** (e.g. `Multi-Strand SSG`). Keep numbers and dimensions in **named custom fields** — do not cram geometry into `Value`.

### Simulation hookup fields (Step 4 — after SUBCKT is linked)

These are what KiCad/ngspice use. Incomplete hookup looks like `Sim.Library` set but `Sim.Name = <unknown>`.

| Field | Example when complete |
|-------|------------------------|
| `Sim.Device` | `SUBCKT` |
| `Sim.Library` | `.../Bedini_Trifilar.lib` |
| `Sim.Name` | `BEDINI_TRIFILAR` |
| `Sim.Pins` | `1=P1 2=P2 3=T1 4=T2 5=S1 6=S2` |
| `Spice_Model` | `BEDINI_TRIFILAR` |
| `Spice_Primitive` | `X` |
| `Spice_Lib` | `.../Bedini_Trifilar.lib` |

Typing only `Sim.Library` in the property list is **not** enough — finish via **Simulation Model…** (Option A) or **Apply simulation model** (Option B/C below).

---

## Step 1 — Fix the symbol (pins and reference)

The library symbol must have **numbered, named pins** before simulation works.

### 1.1 Open Symbol Editor

1. KiCad main window → **Symbol Editor**.
2. Load **Custom_Inductors** (`Custom_Inductors.kicad_sym` in `sym-lib-table`).
3. Open **Bedini_Coil_1**.

### 1.2 Assign pin numbers and names

| Pin # | Name | Electrical role | Typical Bedini net |
|-------|------|-----------------|------------------|
| 1 | `P1` | Primary start | P (primary battery +) |
| 2 | `P2` | Primary end | C (collector / switching) |
| 3 | `T1` | Trigger start | T (base feedback via R7) |
| 4 | `T2` | Trigger end | E (emitter / ground) |
| 5 | `S1` | Secondary start | P |
| 6 | `S2` | Secondary end | C (diodes to charge batteries) |

**Note:** Pin 3 is named `T1` (trigger node) while the component reference is also `T1` — confusing in conversation but fine for simulation.

### 1.2a R7 (trigger sensitivity pot) — do not leave pin 1 open

**R7** is a **1 kΩ pot** between the **Q1 base bias node** (same net as **R3**, pin 3) and the **trigger winding** (wiper → coil pin `T1`, pin 2).

| R7 pin | Role | Connects to |
|--------|------|-------------|
| 1 (`r0`) | Track end | **Same net as pin 3** (rheostat: tie 1 ↔ 3 on the base side) |
| 2 (wiper) | Wiper | Trigger coil pin `T1` |
| 3 (`r1`) | Track end | Q1 base / R3 junction |

An earlier revision had **pin 1 wired to a short stub with no other connection** (`unconnected-_R7-Pad1_` in the netlist). That is an **incomplete schematic**, not normal Bedini practice — it confuses SPICE and ERC. **Pin 1 must join pin 3’s net** so the pot acts as a variable resistor between base bias and trigger feedback.

If you inherit an old copy of the schematic, verify in the netlist that R7 has **no `unconnected-*` net**.

### 1.3 Pin position vs coil graphics (Bedini_Coil_1)

Pin **electrical roles** are defined by number and name, not by which drawn coil bump they sit on.

From `Custom_Inductors.kicad_sym` pin coordinates (more negative X = further left):

| Pin # | X on symbol | On graphic |
|-------|-------------|------------|
| 3, 4 | −3.81 | Left stub (outside left coil bump) |
| 1, 2 | −2.54 | Left coil bump — **primary** |
| 5, 6 | +2.54 | Right side — **secondary** |

The **middle** coil graphic (≈ −1.27) has **no pins** — it is decorative.

**Physical winding:** When you build the coil, connect each physical strand to the pin pair you assigned. Document which strand goes to which pins on the symbol or in build notes.

### 1.4 Change default reference prefix L → T

1. Select the **Reference** property on the symbol.
2. Change **`L`** → **`T`**.
3. Save the library.

Existing schematic instances (e.g. **T1**) keep their reference.

### 1.5 Refresh schematic instance

- Accept library update if prompted.
- Enable **Show pin numbers** while verifying wiring.
- **Exclude from simulation** must be **unchecked**.

---

## Step 2 — Add design-parameter fields on T1

1. Schematic → select **T1** → **Properties**.
2. **Add property** for each design field (table above).
3. Set **Value** to a short label (e.g. `Multi-Strand SSG`) — not the geometry.
4. Save the schematic.

These fields are your **design record** for AI analysis later. They do not enable simulation.

---

## Step 3 — Create the SUBCKT library file

### 3.1 File location

Project metadata (optional):

```
<project>/kicad_ai/subckt/Bedini_Trifilar/
```

Shared library (example):

```
~/Development/Local/kicad_ai_library/libs/Bedini_Trifilar.lib
```

Use a **stable path** and **consistent spelling** (`Trifilar`, not `Trfilar`). `Sim.Library` / `Spice_Lib` must match the real filename.

### 3.2 Starter SUBCKT (ngspice-compatible)

**Homebrew ngspice does not accept `Rser=` on inductor lines** (LTspice-style). Use separate **R + L** in series:

```spice
* Bedini SSG — trifilar air-core coil (STARTER MODEL — tune L/R/k)
* Ports: P1 P2 = primary, T1 T2 = trigger, S1 S2 = secondary
.SUBCKT BEDINI_TRIFILAR P1 P2 T1 T2 S1 S2

* Primary
Rrp P1 n_p 1.5
Lp  n_p P2 3m

* Trigger
Rrt T1 n_t 0.15
Lt  n_t T2 30u

* Secondary
Rrs S1 n_s 1.5
Ls  n_s S2 3m

* Mutual coupling (tightly twisted trifilar on same bobbin)
Kpt Lp Lt 0.98
Kps Lp Ls 0.98
Kts Lt Ls 0.98

.ENDS BEDINI_TRIFILAR
```

### 3.3 Verify with ngspice (macOS)

KiCad on Mac **does not ship a terminal `ngspice` binary** — `.../PlugIns/sim/ngspice` is a **folder** of codec modules, not an executable. Use Homebrew:

```bash
brew install ngspice
```

**Load-only check** (SUBCKT file alone):

```bash
ngspice -b "/path/to/Bedini_Trifilar.lib"
```

If you see only:

```text
Error: incomplete or empty netlist … no simulations run!
```

and **no** `unknown parameter` or `unknown subckt` — the file **parsed OK**. Batch mode expects a full circuit with analysis commands; a `.lib` with only `.SUBCKT` is intentionally incomplete.

**Instantiation check** (recommended):

```bash
ngspice -b <<'EOF'
.include "/path/to/Bedini_Trifilar.lib"
X1 1 2 3 4 5 6 BEDINI_TRIFILAR
V1 1 0 DC 0
.end
EOF
```

Success = no `Error:` lines about unknown parameters or subcircuits.

| Message | Meaning |
|---------|---------|
| `unknown parameter (rser)` | Use separate R + L (see 3.2) |
| `incomplete or empty netlist` on lib-only load | Usually **OK** — syntax passed |
| `unknown subckt` | Wrong model name or file path |

### 3.4 Starter electrical ranges (ballpark)

| Winding | Turns (example) | L (starter) | R (starter) |
|---------|-----------------|-------------|-------------|
| Primary | 400–600 | 1–10 mH | 0.5–3 Ω |
| Trigger | 30–80 | 10–100 µH | 0.05–0.5 Ω |
| Secondary | 400–600 | 1–10 mH | 0.5–3 Ω |
| Coupling k | — | 0.95–0.99 | — |

### 3.5 Optional documentation

Create `<project>/kicad_ai/subckt/Bedini_Trifilar/assumptions.md` — same pattern as `kicad_ai/subckt/BD243C/`.

---

## Step 4 — Hook T1 to the SUBCKT

Three ways to complete simulation hookup. All should produce the **simulation fields** listed in the overview.

### Option A — KiCad Simulation Model editor (manual)

1. Select **T1** → **Properties** → **Simulation Model…**
2. **Device type:** SUBCKT  
3. **Model source:** from file  
4. **File:** full path to `Bedini_Trifilar.lib`  
5. **Model name:** `BEDINI_TRIFILAR`  
6. **Pin assignments:** `1=P1 2=P2 3=T1 4=T2 5=S1 6=S2`  
7. OK → save schematic.

### Option B — KiCad AI Assistant + artifact catalog (recommended)

The assistant **Apply simulation model** looks up the `.lib` in `catalog.json` by the symbol **Value** field (`Multi-Strand SSG`), then writes all `Sim.*` / `Spice_*` fields (same as BD243C).

**Prerequisites:**

- `artifact_library_path` in `~/kicad_ai_config.json` points at your library (e.g. `~/Development/Local/kicad_ai_library`).
- `.lib` registered under part **`Multi-Strand SSG`** (must match T1 **Value** exactly).

**Register the lib** (one-time, from KiCad AI Integration repo):

```bash
cd /Users/edbecnel/Development/GitHub/KiCad_AI_Integration

PYTHONPATH=src python3 <<'PY'
from pathlib import Path
from context.artifacts.store import ArtifactStore, ProjectContextInfo, ComponentRef

LIB = Path("/Users/edbecnel/Development/Local/kicad_ai_library/libs/Bedini_Trifilar.lib")
PROJECT = Path("/Users/edbecnel/Development/Local/Bedini_Self_Oscillator/Bedini_SSG_Radiant_Oscillator.kicad_pro")
LIBRARY = Path("/Users/edbecnel/Development/Local/kicad_ai_library")

store = ArtifactStore(LIBRARY)
entry = store.register_lib(
    LIB,
    "Multi-Strand SSG",
    "user_manual",
    ProjectContextInfo(
        project_pro_path=PROJECT,
        schematic_paths=[PROJECT.parent / "Bedini_SSG_Radiant_Oscillator.kicad_sch"],
    ),
    ComponentRef(reference="T1", sheet_path="Bedini_SSG_Radiant_Oscillator.kicad_sch"),
    tier="context_synthesized",
)
print("Registered:", entry.id)
print("Catalog file:", entry.file)
PY
```

Replace paths if your library or project live elsewhere. You **must** `cd` to the integration repo so `PYTHONPATH=src` finds the `context` package — do not use a placeholder like `/path/to/...`.

Confirm:

```bash
grep -A6 '"part": "Multi-Strand SSG"' ~/Development/Local/kicad_ai_library/catalog.json
```

Look for `"type": "lib"`.

**Apply hookup:**

1. KiCad AI Assistant → open Bedini project → **Refresh context**  
2. **Simulation** panel → select **`Multi-Strand SSG`** row  
3. **Apply simulation model…**

If the schematic was open in KiCad: **File → Revert** on that sheet to reload properties.

### Option C — Quick fix if Apply cannot find the lib

`apply_simulation_model_for_part` checks the artifact catalog **or** the symbol’s **`Spice_Lib`** field (not `Sim.Library` alone).

Add on T1:

```
Spice_Lib = /full/path/to/Bedini_Trifilar.lib
```

Then retry **Apply simulation model** (Option B steps).

### What does *not* auto-apply

| Assistant action | Custom coil T1? |
|------------------|-----------------|
| **Apply built-in models** | No — only R/C/L/diodes/batteries |
| **Refresh context** (builtin sim write) | No — does not complete SUBCKT hookup |
| **Generate SUBCKT** | For datasheet-backed parts today; coil geometry fields not yet used as input |

### Expected fields after successful hookup

```
Sim.Device       = SUBCKT
Sim.Library      = .../Bedini_Trifilar.lib  (or catalog copy e.g. Multi-Strand_SSG.lib)
Sim.Name         = BEDINI_TRIFILAR
Sim.Pins         = 1=P1 2=P2 3=T1 4=T2 5=S1 6=S2
Spice_Model      = BEDINI_TRIFILAR
Spice_Primitive  = X
Spice_Lib        = .../Bedini_Trifilar.lib
```

`Sim.Name = <unknown>` means hookup is **incomplete** — finish Option A, B, or C.

---

## Step 5 — Verify netlist export

### macOS: `kicad-cli` is not on PATH by default

KiCad installs the CLI inside the app bundle. Use the **full path** or set config / alias:

```bash
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli version
```

**Option 1 — full path (copy/paste):**

```bash
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch export netlist \
  --format spice \
  -o /tmp/bedini.net \
  "/Users/edbecnel/Development/Local/Bedini_Self_Oscillator/Bedini_SSG_Radiant_Oscillator.kicad_sch"
```

Use the **`.kicad_sch`** file (not `.kicad_pro`).

**Option 2 — shell alias** (add to `~/.zshrc`):

```bash
alias kicad-cli='"/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"'
```

**Option 3 — KiCad AI Assistant config** (`~/kicad_ai_config.json`):

```json
"kicad_cli": "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
```

Then **Refresh context** uses the CLI for netlist export automatically.

### What to check in the netlist

The `-o` flag in the export command above writes the netlist to a file **you choose**. In that example the output file is:

```text
/tmp/bedini.net
```

That is an absolute path in macOS’s temporary folder — not relative to your project. Run `grep` on **that same file**:

```bash
grep -E 'BEDINI_TRIFILAR|\.include' /tmp/bedini.net
```

The pattern `\.include` matches **lines inside the netlist** that pull in `.lib` files (not a path on disk to search).

**Example good output** (your paths may differ):

```text
.include "/Users/edbecnel/Development/Local/kicad_ai_library/libs/BD243C.lib"
.include "/Users/edbecnel/Development/Local/kicad_ai_library/libs/Multi-Strand_SSG.lib"
XT1 Net-_ChargeBT1--_ Net-_D1-A_ ... BEDINI_TRIFILAR
```

You want:

- At least one `.include` line pointing at your coil `.lib` (`Multi-Strand_SSG.lib` or `Bedini_Trifilar.lib`)
- One device line ending in `BEDINI_TRIFILAR` (prefix `X` + reference, e.g. `XT1`)

**Optional — write next to your project instead of `/tmp`:**

```bash
NETLIST="/Users/edbecnel/Development/Local/Bedini_Self_Oscillator/kicad_ai/exports/bedini.net"
mkdir -p "$(dirname "$NETLIST")"
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch export netlist \
  --format spice \
  -o "$NETLIST" \
  "/Users/edbecnel/Development/Local/Bedini_Self_Oscillator/Bedini_SSG_Radiant_Oscillator.kicad_sch"
grep -E 'BEDINI_TRIFILAR|\.include' "$NETLIST"
```

### Interpreting exit codes and stderr

| Output | Meaning |
|--------|---------|
| `Fontconfig warning: ...` | Harmless on macOS — ignore |
| `No simulation model definition found` (×6 on Bedini) | Usually **R1–R6** with `Sim.Type=RESISTOR` — KiCad 10 rejects that type; remove `Sim.Type` and keep `Sim.Device=R` + `Sim.Params=r=…` |
| `No simulation model definition found` (other) | Some symbol(s) still lack models — check which refs KiCad names |
| Exit code **2** with a non-empty netlist | **Partial export** — netlist may still be usable; read the file |
| Exit code **0** | Clean export |

T1 can be correct in the netlist while other parts still trigger warnings.

### Assistant check

**KiCad AI Assistant** → **Refresh context** → **Simulation** panel — `Multi-Strand SSG` should leave the missing-models list when hookup is complete.

Remaining issues may be other parts (e.g. BD243C paths), not standard passives or diodes like `1N4007`.

---

## Step 6 — First simulation run

The SPICE simulator is **inside the Schematic Editor**, not the KiCad project manager home screen.

### Before simulating (if the assistant edited the schematic)

KiCad does **not** have **File → Reload**. If the schematic was already open while the assistant (or an external tool) changed `Bedini_SSG_Radiant_Oscillator.kicad_sch` on disk:

1. In the **Schematic Editor**: **File → Revert** (discards unsaved editor changes and reloads from disk), **or**
2. Close the schematic tab and reopen it from the project.

Then run the simulator.

1. Open your project in KiCad.
2. Open the **Schematic Editor** (edit `Bedini_SSG_Radiant_Oscillator.kicad_sch`).
3. Menu: **Inspect → Simulator** (some versions label it **Simulator…**).

A separate **Simulator** window opens (ngspice behind the scenes).

### Configure transient analysis

1. In the Simulator window: **New analysis tab** (toolbar icon or **Ctrl+N** / **⌘N** on Mac).
2. **Analysis type:** `tran` (transient).
3. Set **Time step** and **Final time** (start small, e.g. step `1u`, final `10m` — tune for your oscillator).
4. Click **Run** (play/arrow button in the Simulator toolbar).

### Probe waveforms

- Use the **probe** tool in the Simulator window to click nets (voltage) or pins (current).
- Useful signals: Q1 collector (`C` net), base (`T` net), primary supply.

### If simulation fails to start

- Confirm Step 5 netlist includes `BEDINI_TRIFILAR` and `.include` lines.
- Check Simulator output panel for missing models or convergence errors.
- **`unconnected-_R7-Pad1_` in netlist or log** — tie **R7 pin 1** to **pin 3** (base bias net); see §1.2a.
- **`Timestep too small` / `trouble with xq1`** — stiff BJT + coil; try TRAN step `10u`, final `5m`, max step `10u`, and add schematic directive `.options method=gear maxord=2 gmin=1e-10`.
- Save the schematic before simulating if KiCad prompts you.

### What to look for

1. Does Q1 switch (collector voltage oscillating)?
2. Any absurd currents (model values unrealistic)?
3. If no oscillation: tune **Lt** and **Lp** first in `Bedini_Trifilar.lib` / `Multi-Strand_SSG.lib`.

Document trials in `assumptions.md` or the Engineering Notebook.

---

## Step 7 — Iterate

### Manual loop

1. Change geometry / turn fields on T1.  
2. Recompute or hand-edit L/R in `.lib`.  
3. Re-export netlist → re-simulate.

### AI-assisted loop (direction)

1. **Chat** or **AERF** with T1 custom fields — estimate Lp, Lt, Ls, R, k from N, AWG, Coil_ID, Coil_OD, Coil_Width.  
2. Update `Bedini_Trifilar.lib` and `assumptions.md`.  
3. Re-apply simulation model if paths changed → re-simulate.

---

## Checklist

- [ ] Pins 1–6 named P1/P2/T1/T2/S1/S2; wiring matches P/C/T/E nets  
- [ ] Reference prefix **T** in library  
- [ ] Design fields on T1 (`Value`, `N_*`, `Coil_*`, `Wire_Gauge`, `Coupling_k`)  
- [ ] `Bedini_Trifilar.lib` with ngspice-compatible R+L (no `Rser=`)  
- [ ] ngspice instantiation test passes  
- [ ] SUBCKT hookup complete (`Sim.Name` = `BEDINI_TRIFILAR`, not `<unknown>`)  
- [ ] Catalog registration for `Multi-Strand SSG` (if using assistant Apply)  
- [ ] Netlist exports without T1 errors  
- [ ] First transient simulation run  

---

## Related docs

- [Testing With Your KiCad Project](./Testing_With_Your_KiCad_Project.md)  
- [Feature Overview](./Feature_Overview.md) — Simulation / SUBCKT gap-fill  
- [Netlist Gap Fill](../Specifications/Netlist_Gap_Fill.md)  
- Blocking Oscillator: `docs/Engineering_Knowledge/Circuit_Families/Blocking_Oscillator/`

---

## Why not built-in `Sim.Device=L`?

A single inductor cannot represent three coupled windings. ngspice needs three inductors, mutual `K` coupling, and series resistance per winding — packaged in a **SUBCKT**, not KiCad’s built-in passive auto-models.

---

*Bedini SSG Radiant Oscillator — Custom_Inductors:Bedini_Coil_1 / T1.*
