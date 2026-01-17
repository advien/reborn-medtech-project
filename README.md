# Reborn — Human-in-the-loop Active Elbow Orthosis (MVP)

**One-liner:** Reborn is a system-level R&D case for a **safety-first, human-in-the-loop active elbow orthosis**, connecting EMG/IMU sensing, signal quality checks, deterministic decision logic, and optional ML — with predictable failure behavior as the primary goal.

---

## TL;DR
Reborn explores how to design an assistive robotic system where:
- **assist flexion** is the MVP target behavior,
- sensors (especially EMG) are assumed to be **noisy and unreliable**,
- the system is engineered to **degrade gracefully** under uncertainty,
- ML is **optional and bounded**, never the controller and never the safety authority.

This is not a medical product claim. It is an engineering case focused on system design under real-world constraints.

---

## Problem / Why this matters
In assistive devices, errors are not just “bad metrics” — they can be **unsafe physical actions**.

Real-world sensing is messy:
- EMG changes with electrode placement, sweat, fatigue, and posture
- IMU is useful for motion context, but can drift and produce artefacts
- Humans adapt to the system, and the system must remain predictable

Reborn is built around a core idea:

> In assistive systems, the worst failure is not “no help” — the worst failure is **unexpected help**.

---

## MVP scope (what is in / what is out)

### In (MVP)
- **Device:** active elbow orthosis (1 DOF)
- **Control goal:** **assist flexion**
- **Signals:** EMG + IMU  
  - Stage 1: EMG-only  
  - Stage 2: IMU-only  
  - Stage 3: EMG+IMU fusion
- **Decision logic:** deterministic (state machine / rule-based), confidence-gated
- **Safety model:** explicit fallback + emergency behavior
- **Data work:** hypothesis-driven recordings and analysis (not dataset-driven)

### Out (intentionally excluded from MVP)
- Clinical validation, certification, or medical claims
- Product-grade mechanical design / ergonomics
- ML-driven autonomous control (black-box control)

These exclusions are deliberate to keep the system explainable, testable, and safe by design.

---

## System overview (layers & dataflow)

```text
User (muscle intent)
   │
   ▼
Sensors (EMG + IMU)
   │
   ▼
Signal QC / Preprocessing
- contact quality checks (EMG)
- filtering / normalization
- artefact handling (IMU)
   │
   ▼
State estimation / Features
   │
   ├──► (optional) ML inference
   │        - intent classification (flex / no flex)
   │        - confidence / uncertainty
   │        - anomaly detection (invalid signal)
   │
   ▼
Decision logic (safety-first)
- deterministic state machine
- confidence gating
- conservative behavior under ambiguity
   │
   ▼
Actuation (assist flexion)
   │
   ▼
Safety layer (always-on)
- torque/position/velocity limits
- emergency stop / cutoff
- fallback modes
   │
   ▼
User feedback + Logging
- state (OK / degraded / fallback)
- safety events
- data for iteration