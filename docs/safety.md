# Reborn — Safety Specification (MVP)

## Purpose of this document
This document defines the **safety philosophy, constraints, and failure handling**
for the Reborn MVP — an active elbow orthosis with assistive flexion.

Safety is treated as a **first-class system requirement**, not as an afterthought
or a post-ML correction layer.

---

## Core safety principles

1. **Safety overrides functionality**
   - Any assistive behavior is secondary to user safety.

2. **Uncertainty reduces autonomy**
   - When the system is unsure, it must do less — not more.

3. **Fail silent, not aggressive**
   - Inaction or passive mode is preferred to incorrect action.

4. **Deterministic > intelligent**
   - Safety logic is rule-based and explainable.
   - ML is never responsible for safety decisions.

---

## Safety layer positioning

The Safety Layer is:
- always active
- independent of ML
- capable of overriding *any* other system component

```text
Sensors / ML / Decision Logic
          │
          ▼
     Safety Layer
          │
          ▼
      Actuation

No component can bypass the Safety Layer.

⸻

Safety-controlled parameters (MVP)

The following parameters are hard-limited:
	•	joint angle (min / max)
	•	angular velocity
	•	assistive torque / force
	•	activation duration
	•	command update rate

Limits are defined conservatively and may be lowered during experiments.

⸻

Safety states

The system operates in explicit safety-related states:
	•	Idle
	•	no assist
	•	passive monitoring only
	•	Assist
	•	assistive flexion enabled
	•	all safety checks active
	•	Degraded
	•	reduced assist level
	•	triggered by uncertainty or partial signal loss
	•	Fallback
	•	assist disabled
	•	system remains responsive but passive
	•	Emergency stop
	•	immediate actuator shutdown
	•	requires explicit reset

State transitions are deterministic and logged.

⸻

Safety triggers

Signal-related triggers
	•	EMG signal invalid or unstable
	•	IMU data missing or inconsistent
	•	desynchronization between sensors

System-related triggers
	•	latency above threshold
	•	missed control updates
	•	internal watchdog timeout

Physical triggers
	•	joint limit reached
	•	unexpected resistance
	•	actuator saturation

Any trigger can force transition to Degraded, Fallback, or Emergency stop.

⸻

ML-specific safety rules

ML outputs are treated as advisory signals only.

Rules:
	•	ML cannot directly control actuators
	•	ML output must include confidence or validity flag
	•	absence of ML output is valid and safe

If ML output is:
	•	uncertain → reduce assist
	•	invalid → disable assist
	•	missing → fallback mode

ML failure must never cause unsafe motion.

⸻

Human-in-the-loop safety considerations

The human contributes to safety by:
	•	adapting muscle activation
	•	responding to system feedback
	•	learning system behavior

Therefore:
	•	system behavior must be predictable
	•	assist onset/offset must be smooth
	•	sudden transitions are avoided

Safety is a shared responsibility, but final authority remains with the system.

⸻

Logging and traceability

All safety-relevant events are logged:
	•	state transitions
	•	trigger activations
	•	emergency stops
	•	limit violations

Logs are used for:
	•	post-session analysis
	•	system tuning
	•	understanding near-miss scenarios

⸻

Explicit non-goals (MVP)

This safety specification does not attempt to:
	•	comply with medical device regulations
	•	replace clinical risk analysis
	•	certify the system for real patients

It is a research and engineering safety model, not a product claim.

⸻

Design reminder

In assistive systems, the worst failure is not “no help” —
the worst failure is unexpected help.

Reborn is designed to avoid that failure first.
