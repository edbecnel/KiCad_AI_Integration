# Oscillator Analysis Knowledge Base

[Home](../../../../README.md) · [Project Index](../../../../PROJECT_INDEX.md) · [Engineering Knowledge](../../README.md) · [Circuit Families](../README.md) · Blocking Oscillator

## Purpose

This collection of engineering documents provides a progressively deeper understanding of self-oscillating blocking oscillators such as the Bedini SSG Radiant Oscillator.

The documents are intended to serve both as engineering reference material and as semantic knowledge for the KiCad AI Integration project.

---

# Document Roadmap

## [00 - Circuit Identification](00 - Circuit Identification.md)

The AI first determines **what the circuit is**.

Topics include:

- Circuit family
- Topology
- Functional blocks
- Inputs and outputs
- Energy conversion chain

---

## [01 - Basic Oscillation](01 - Basic Oscillation.md)

Explains **why the circuit oscillates**.

Topics include:

- Startup
- Positive feedback
- Trigger winding
- Transistor switching
- Oscillation cycle

---

## [02 - Energy Flow](02 - Energy Flow.md)

Explains **where the energy goes**.

Topics include:

- Energy storage
- Flyback energy
- Battery charging
- Energy losses
- Power flow

---

## [03 - Physical Principles](03 - Physical Principles.md)

Explains the magnetic and physical behavior.

Topics include:

- Magnetic field build-up
- Inductive collapse
- Mutual inductance
- Transformer coupling
- Faraday's Law

---

## [04 - Component Roles](04 - Component Roles.md)

Explains the engineering purpose of every component.

Topics include:

- Functional role
- Component interaction
- Component selection
- Possible substitutions

---

## [05 - Operating Modes](05 - Operating Modes.md)

Explains how the circuit behaves under different conditions.

Topics include:

- Startup
- Normal operation
- Saturation
- Weak battery
- Missing battery
- Fault conditions

---

## [06 - System Behavior](06 - System Behavior.md)

Explains the complete electro-mechanical system.

Topics include:

- Rotor interaction
- Magnetic timing
- Mechanical loading
- Thermal behavior
- Environmental influences

---

## [07 - Engineering Analysis](07 - Engineering Analysis.md)

Demonstrates how an experienced engineer evaluates the design.

Topics include:

- Performance analysis
- Failure analysis
- Simulation interpretation
- Design improvements
- Troubleshooting
- Optimization

---

# Recommended Reading Order

1. [00 - Circuit Identification](00 - Circuit Identification.md)
2. [01 - Basic Oscillation](01 - Basic Oscillation.md)
3. [02 - Energy Flow](02 - Energy Flow.md)
4. [03 - Physical Principles](03 - Physical Principles.md)
5. [04 - Component Roles](04 - Component Roles.md)
6. [05 - Operating Modes](05 - Operating Modes.md)
7. [06 - System Behavior](06 - System Behavior.md)
8. [07 - Engineering Analysis](07 - Engineering Analysis.md)

Each level assumes familiarity with the preceding documents.

---

# KiCad AI Integration

The KiCad AI Plugin should emulate the reasoning process represented by these documents.

Rather than immediately interpreting simulation results, the AI should progressively answer:

1. What is this circuit?
2. How does it operate?
3. Where does energy flow?
4. What physical principles govern it?
5. What role does each component perform?
6. How does it behave under different operating conditions?
7. How does the complete system function?
8. What engineering conclusions can be drawn?

This mirrors the reasoning process of an experienced electrical engineer.

See also: [How the Bedini SSG Oscillates Without a Capacitor](../../../Development/Reference_Notes/How_the_Bedini_SSG_Oscillates_Without_a_Capacitor.md) (reference note).

---

## Recognition signatures

Heuristic signals used by the circuit family classifier (`src/reasoning/classifier.py`):

| Signal | Typical patterns |
|--------|------------------|
| Switching device | BJT or MOSFET symbol (`Device:Q_*`) driving a transformer or inductor |
| Magnetic storage | Transformer (`Device:T_*`) or inductor (`Device:L_*`) with separate primary / trigger / secondary windings |
| Feedback path | Trigger or feedback winding net names (`trigger`, `feedback`, `coil`) |
| Topology | Single active switch, transformer energy storage, self-oscillating drive (no external clock) |
| Net naming | `coil`, `flyback`, `oscillator`, or Bedini-style winding labels |

**Distinguishing from related families:**

- **Flyback converter** — often has rectified secondary output and duty-cycle control; blocking oscillator is usually self-triggered with a feedback winding
- **Buck / boost** — inductor on switching node without transformer isolation; no separate trigger winding

Machine-readable rules mirror this section in [`families.json`](../families.json) under `recognition`.
