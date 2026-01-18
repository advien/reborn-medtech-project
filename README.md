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

Human-in-the-loop (why the human is part of control)

The user is not just a signal source. The user is part of the control loop:
	•	the system must remain learnable through interaction
	•	uncertainty must be visible via feedback (status, fallback)
	•	the system must behave predictably when signals degrade

Design intent:

When confidence is low, the system should do less — not guess more.

⸻

Safety & failure modes (design intent)

Reborn is designed around the question: What does the system do when everything goes wrong?

Typical failures considered:
	•	EMG: poor contact, drift, fatigue, cross-talk, saturation, dropouts
	•	IMU: drift, artefacts under sudden motion, sensor misalignment
	•	System: latency spikes, missed updates, desync
	•	Human: inconsistent intent, unexpected motion patterns

Safety policies (MVP):
	•	Confidence gating: uncertainty reduces or disables assist
	•	Fallback modes: safe idle / passive mode / limited assist
	•	Hard limits: torque, speed, angle
	•	Logging-first: safety events and degradations are recorded for analysis

⸻

Role of ML (and non-role)

ML may help with:
	•	confidence/uncertainty estimation
	•	invalid-signal detection
	•	intent classification (flex vs no flex)
	•	reducing false triggers via EMG+IMU fusion

ML must NOT do in MVP:
	•	directly drive actuators
	•	replace deterministic decision logic
	•	replace the safety layer
	•	“guess” under uncertainty

ML is advisory and bounded.
⸻

Data collection (summary)

Data collection is designed to expose failure modes, not to maximize dataset size.

Stages:
	1.	EMG-only: repeatable flexion tasks, varying activation levels, multi-session drift
	2.	IMU-only: slow/fast motion, holds, artefacts
	3.	Fusion: complementary degradation (EMG bad / IMU clean and vice versa)

“Bad data” is collected intentionally to validate safe degradation behavior.

⸻

Milestones (4–8 weeks)
	•	M1: Architecture + safety spec + repo structure
	•	M2: Data protocol + first recordings (EMG-only)
	•	M3: Baseline deterministic decision logic (state machine) + logs
	•	M4: IMU pipeline + robustness comparison (EMG vs IMU)
	•	M5: Fusion + confidence gating
	•	M6: Minimal demo + video + results summary

⸻

Repo structure (planned)
	•	docs/
	•	architecture.md
	•	safety.md
	•	data-protocol.md
	•	experiments.md
	•	notebooks/
	•	01_emg_qc_and_baselines.ipynb
	•	02_imu_baselines.ipynb
	•	03_fusion_confidence.ipynb
	•	prototype/
	•	firmware / scripts (later)
	•	assets/
	•	diagrams, photos, demo video links

⸻

What this project demonstrates
	•	system design across sensing → decision → actuation
	•	safety-first engineering and explicit failure handling
	•	restrained, pragmatic ML usage (bounded and optional)
	•	human-in-the-loop reasoning and user trust considerations
	•	documentation quality suitable for R&D collaboration

This is not a demo gadget.
It is a control system designed around uncertainty, safety, and human interaction.