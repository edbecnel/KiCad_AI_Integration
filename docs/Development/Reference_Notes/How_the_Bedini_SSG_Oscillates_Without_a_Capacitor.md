# How the Bedini SSG Oscillates Without a Capacitor

One of the most interesting aspects of the Bedini SSG is that it oscillates **without using a capacitor**. Unlike many transistor oscillator circuits that rely on an RC timing network, the Bedini SSG uses the **inductor (coil)** and **magnetic feedback** as the timing element.

The oscillation is controlled by the interaction of four primary elements:

1. The trigger winding
2. The transistor's current gain
3. The base resistor network
4. The magnetic field building and collapsing in the coil

The transformer (T1) contains separate power and trigger windings. The trigger winding provides regenerative feedback to the transistor, creating a self-sustaining oscillation.

---

# Oscillation Cycle

## 1. Initial Turn-On

When power is first applied, a small current flows through the base resistor into the transistor.

```
Battery
   │
 Base Resistor
   │
 Base of Q1
```

This small current turns the transistor on slightly.

---

## 2. Current Begins Flowing Through the Power Winding

As the transistor begins conducting, current flows through the primary (power) winding.

```
Battery
   │
Primary Winding
   │
Collector
   Q1
Emitter
   │
Ground
```

This current builds a magnetic field around the coil.

---

## 3. Magnetic Feedback Increases Conduction

The increasing magnetic field induces a voltage into the trigger winding.

If the winding polarity (dot convention) is correct, this induced voltage **adds to the transistor's base drive**.

The result is positive feedback:

```
Small collector current
        ↓
Increasing magnetic field
        ↓
Trigger winding produces voltage
        ↓
More base current
        ↓
Greater collector current
        ↓
Stronger magnetic field
```

The transistor rapidly turns fully on.

---

## 4. Current Reaches Its Maximum

The collector current cannot continue increasing indefinitely.

Eventually one or more of the following occurs:

- The transistor approaches saturation.
- The magnetic core begins to saturate (if a magnetic core is used).
- The rate of current increase (di/dt) decreases.

---

## 5. Trigger Voltage Collapses

The trigger winding only generates voltage while the magnetic field is **changing**.

When the current stops increasing rapidly,

```
dI/dt → 0
```

the induced trigger voltage disappears.

Without this additional base drive, the transistor begins to turn off.

---

## 6. The Transistor Switches Off

Collector current suddenly stops.

The magnetic field stored in the primary winding now collapses.

A collapsing magnetic field produces a high-voltage flyback pulse.

---

## 7. Flyback Energy Charges the Battery

The flyback pulse is directed through the diode into the charging battery.

This transfers the stored magnetic energy into the secondary battery.

---

## 8. The Cycle Repeats

Once the magnetic field has completely collapsed:

- The transistor is fully off.
- The base resistor again provides a small bias current.
- The entire process repeats.

This creates a continuous self-oscillating cycle.

---

# What Determines the Oscillation Frequency?

Unlike an RC oscillator, the Bedini SSG's frequency is primarily determined by how quickly current builds in the primary winding.

The main factors include:

- Primary winding inductance
- Trigger winding inductance and coupling coefficient
- Supply voltage
- Base resistor values
- Transistor characteristics (gain, saturation, storage time)
- Magnetic core material (or air core)
- Mechanical rotor speed (in the complete Bedini SSG with magnets)
- Load presented by the charging battery

Higher supply voltage generally increases frequency because current rises more quickly.

Greater inductance generally lowers frequency because current takes longer to build.

---

# Why No Capacitor Is Required

Many oscillators use an RC timing network.

```
Resistor + Capacitor
```

The Bedini SSG instead uses:

```
Inductor + Magnetic Feedback
```

The inductor stores energy in its magnetic field.

The changing magnetic field induces a voltage into the trigger winding.

This regenerative magnetic feedback automatically turns the transistor on and off.

Therefore, the inductor itself becomes the timing element.

---

# Engineering Classification

From an engineering standpoint, the Bedini SSG is best classified as a:

- Self-oscillating blocking oscillator
- Magnetically coupled blocking oscillator
- Self-oscillating flyback converter

The oscillation is produced by regenerative magnetic feedback rather than by an RC timing network.

---

# Implications for the KiCad AI Plugin

Rather than treating the schematic as simply a collection of components, the AI plugin should attempt to recognize higher-level circuit topologies.

For this circuit, the plugin could automatically identify:

```
Circuit Topology:
    Self-Oscillating Blocking Oscillator

Power Switch:
    Q1

Energy Storage Element:
    Primary Winding

Feedback Element:
    Trigger Winding

Flyback Path:
    D1

Energy Destination:
    Charging Battery

Oscillation Method:
    Regenerative Magnetic Feedback

Timing Element:
    Primary Inductance
```

Most of this information should be inferred automatically from the circuit topology and component connectivity. The schematic itself only needs to contain information representing the designer's intent or details that cannot be reliably derived automatically.