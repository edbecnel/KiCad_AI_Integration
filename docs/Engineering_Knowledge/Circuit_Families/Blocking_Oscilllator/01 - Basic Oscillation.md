---
title: Basic Oscillation
level: 1
category: Oscillator Analysis
circuit_family: Blocking Oscillator
status: Draft
tags:
  - electronics
  - oscillators
  - blocking-oscillator
  - bedini
  - flyback
  - transistor
  - engineering
  - knowledge-base
---

# 01 - Basic Oscillation

**Previous:** [[00 - Circuit Identification]]

**Next:** [[02 - Energy Flow]]

**Knowledge Base:** [[README]]

---

# Purpose

Having identified the circuit as a self-oscillating blocking oscillator, the next step is to understand **how the circuit produces continuous oscillation**.

Unlike many oscillators that rely on resistor-capacitor (RC) timing networks or external clock signals, the Bedini SSG uses **regenerative magnetic feedback** to repeatedly switch the transistor on and off.

This document explains the sequence of events that produces one complete oscillation cycle.

---

# Fundamental Principle

Oscillation occurs because a changing magnetic field induces a voltage into the trigger winding.

That induced voltage temporarily increases the transistor's base current, causing the transistor to conduct even more current through the primary winding.

This creates **positive feedback**, rapidly driving the transistor fully on.

Eventually the magnetic field can no longer continue increasing fast enough to sustain the induced trigger voltage.

Base drive disappears.

The transistor switches off.

The collapsing magnetic field then begins the next cycle.

---

# Why No Capacitor Is Required

Many oscillators use a capacitor to establish timing.

The Bedini SSG does not.

Instead, timing is determined by:

- Primary winding inductance
- Magnetic coupling between windings
- Base resistor values
- Transistor characteristics
- Supply voltage
- Core material

The inductor—not a capacitor—controls the timing of the oscillation.

---

# One Complete Oscillation Cycle

The following sequence repeats continuously.

---

## Stage 1 – Startup

Initially the transistor is off.

A small current flows through the base bias resistor.

This current slightly turns on the transistor.

Result:

- Small collector current begins flowing.

---

## Stage 2 – Magnetic Field Build-Up

Collector current now flows through the primary winding.

A magnetic field begins building around the coil.

As the magnetic field changes, it induces a voltage into the trigger winding.

Result:

- Trigger winding produces base drive.

---

## Stage 3 – Positive Feedback

The trigger winding increases transistor base current.

More base current causes more collector current.

More collector current produces a stronger magnetic field.

A stronger magnetic field induces an even larger trigger voltage.

This regenerative process continues very rapidly.

Result:

- Transistor enters saturation.

---

## Stage 4 – Magnetic Saturation

The magnetic field approaches its maximum value.

Its rate of change slows dramatically.

Since induced voltage depends upon the rate of change of magnetic flux, the trigger winding can no longer provide sufficient base drive.

Result:

- Base current rapidly falls.

---

## Stage 5 – Transistor Turn-Off

Without sufficient base current, the transistor turns off.

Collector current immediately begins decreasing.

The magnetic field surrounding the primary winding collapses.

Result:

- Flyback voltage is produced.

---

## Stage 6 – Flyback Pulse

The collapsing magnetic field generates a voltage of opposite polarity.

This voltage may greatly exceed the supply voltage.

The flyback diode conducts, directing this pulse into the charging battery.

Result:

- Energy leaves the magnetic field.

---

## Stage 7 – Cycle Reset

The magnetic field has now completely collapsed.

No trigger voltage remains.

The base resistor once again provides a small startup current.

The next oscillation cycle begins.

---

# Oscillation Timeline

```text
Base Bias
      │
      ▼
Collector Current Begins
      │
      ▼
Magnetic Field Builds
      │
      ▼
Trigger Winding Produces Voltage
      │
      ▼
Positive Feedback
      │
      ▼
Transistor Saturates
      │
      ▼
Trigger Voltage Falls
      │
      ▼
Transistor Turns Off
      │
      ▼
Magnetic Field Collapses
      │
      ▼
Flyback Pulse
      │
      ▼
Charging Battery
      │
      ▼
Repeat
```

---

# What Determines Oscillation Frequency?

The oscillation frequency is not fixed.

It depends upon several interacting factors, including:

- Supply voltage
- Coil inductance
- Number of trigger winding turns
- Magnetic coupling coefficient
- Core material
- Base resistor values
- Transistor gain
- Battery loading
- Rotor position (complete Bedini SSG)

Changing any of these parameters changes the oscillation frequency.

---

# Common Misconceptions

## The trigger winding powers the transistor.

Incorrect.

The trigger winding only provides feedback.

The energy ultimately comes from the primary battery.

---

## The flyback pulse creates the oscillation.

Incorrect.

The flyback pulse is produced **after** the transistor turns off.

Oscillation is sustained by regenerative magnetic feedback during the field build-up phase.

---

## A capacitor must be hidden somewhere.

Incorrect.

The oscillation is established through inductive behavior and magnetic coupling.

Although small parasitic capacitances exist in all real circuits, they are not responsible for the oscillation mechanism.

---

# AI Recognition Goals

A KiCad AI assistant should recognize:

- The startup mechanism
- The positive feedback loop
- The transistor switching sequence
- The trigger winding's function
- The reason no timing capacitor is required
- The repeating oscillation cycle

The AI should be able to explain the sequence of events without requiring simulation.

Simulation should confirm the explanation—not create it.

---

# Summary

The Bedini SSG is a self-oscillating blocking oscillator that uses regenerative magnetic feedback to repeatedly switch a transistor on and off.

Each oscillation cycle consists of:

1. Startup bias
2. Magnetic field build-up
3. Positive feedback
4. Transistor saturation
5. Turn-off
6. Flyback pulse
7. Reset

Understanding this sequence provides the foundation for analyzing energy transfer, magnetic behavior, and overall system performance.

---

# Questions Answered

- Why does the circuit oscillate?
- Why is no capacitor required?
- How does the transistor switch on and off?
- What role does the trigger winding perform?
- What causes one oscillation cycle to repeat?

# Questions Introduced

The following questions are answered in [[02 - Energy Flow]]:

- Where is energy stored?
- How much energy is transferred each cycle?
- What happens to the stored magnetic energy?
- Where are the major energy losses?
- How does energy move through the entire system?