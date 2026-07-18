# Reborn — System Architecture

## Purpose of this document
This document describes the **system architecture** of the Reborn MVP:
an active elbow orthosis with human-in-the-loop control, based on EMG and IMU signals.

The goal is not to define a final product, but to:
- fix **system intent**
- define **clear module boundaries**
- make assumptions, constraints, and failure handling explicit

This architecture is designed to be:
- modular
- safety-first
- explainable to engineers, not only ML specialists

---

## High-level system view

```text
Human (user)
  │
  │ muscle activation / motion
  ▼
[Sensing Layer]
  │  EMG, IMU
  ▼
[Signal Quality & Preprocessing]
  │
  ▼
[State Estimation / Features]
  │
  ├── (optional) ML inference
  │
  ▼
[Decision Logic]
  │
  ▼
[Actuation]
  │
  ▼
[Safety Layer]  ← always-on
  │
  ▼
Physical interaction + feedback
```

---

## HAL — the spine of the codebase

Everything above the sensing/actuation boundary — `sensing/`, `decision/`, `safety/`, `control/`, `ml/` —
talks only to the interfaces defined in [`reborn/hal/interfaces.py`](../reborn/hal/interfaces.py):

- `SensorSource` — "give me the next sensor frame" (EMG/IMU samples + timestamp).
- `ActuatorSink` — "send this actuator command" (torque/velocity setpoint).

Two backends implement these interfaces:

- `reborn/hal/sim_backend.py` — replays arrays or generators (recorded EMG, synthetic signals) as
  sensor frames, and records actuator commands for later inspection. This is what every
  `sim/*.py` script and notebook uses today.
- `reborn/hal/hardware_backend.py` — will talk to real MyoWare/IMU sensors and an Arduino-driven
  actuator over serial. It is a stub for now.

No code outside `hal/` should import a backend directly or branch on "sim vs hardware." The
control loop, decision logic, and safety layer are constructed once against the interfaces; moving
from simulation to hardware means swapping which backend gets passed in, not rewriting the loop.

See [`sim/run_baseline_loop.py`](../sim/run_baseline_loop.py) for the minimal working example:
sensor source → sensing/QC → decision → safety → actuator sink → logging.

---

## Layer responsibilities

- **Sensing** (`reborn/sensing/`) — filtering, feature extraction, and signal-quality flags
  (contact quality, saturation, dropout). Consumes `SensorFrame`s from a `SensorSource`.
- **Decision** (`reborn/decision/`) — deterministic state machine (Idle / Assist / Degraded /
  Fallback / Emergency stop) plus confidence gating. This is where ML advisory outputs (if any)
  are consulted, never where they take control.
- **Safety** (`reborn/safety/`) — always-on, independent of ML: hard limits (torque/velocity/angle),
  fault detection, and fallback policy selection. Can override any other component. See
  [`safety.md`](safety.md) for the full policy.
- **Control / Plant** (`reborn/control/`, `reborn/plant/`) — closed-loop control, anti-windup,
  robustness under saturation/latency, and the simulated elbow + actuator dynamics. This is the
  phase C work; today these modules are skeletons.
- **ML** (`reborn/ml/`) — bounded, advisory outputs only (intent classification, anomaly detection,
  personalization). Never a controller, never a safety authority. Phase B work; today these
  modules are interface stubs.
- **Logging** (`reborn/logging/`) — records every state transition and safety event for later
  analysis, per [`data-protocol.md`](data-protocol.md).

Human-in-the-loop considerations, failure modes, and the full safety policy are in
[`safety.md`](safety.md). Data collection strategy is in [`data-protocol.md`](data-protocol.md).
The hypothesis-driven experiment plan is in [`experiments.md`](experiments.md). The research
roadmap tying all of this to phases A–D is in [`roadmap.md`](roadmap.md).
