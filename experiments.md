# Reborn — Experiments & Validation Plan (MVP)

## Purpose of this document
This document defines **hypothesis-driven experiments** for the Reborn MVP.

The goal is to:
- validate system behavior under real-world constraints
- observe failure modes explicitly
- ensure safety-first responses are enforced

Experiments are designed to answer **engineering questions**, not to maximize ML metrics.

---

## Experiment philosophy

Each experiment follows the structure:

> Hypothesis → Setup → Procedure → Observations → Expected system behavior

Key rule:
> If an experiment does not change a design decision, it is not needed.

---

## Experiment group A — Signal reliability

### A1. EMG intra-session variability

**Hypothesis**  
EMG amplitude and features vary significantly within a single session, even under similar movements.

**Setup**
- EMG-only mode
- stable electrode placement
- no actuation (monitoring only)

**Procedure**
- repeated slow flexion cycles
- rest → flex → rest
- duration: ~5 minutes

**Observations**
- raw EMG amplitude
- feature variance
- quality flags

**Expected system behavior**
- signal quality flags remain mostly valid
- noticeable variance in EMG features
- no assist triggered unintentionally

**Design implication**
- EMG thresholds must be adaptive or conservative
- raw amplitude is insufficient for control decisions

---

### A2. EMG inter-session drift

**Hypothesis**  
EMG signal characteristics drift between sessions and days.

**Setup**
- identical movement protocol
- sessions on different days

**Procedure**
- repeat A1 protocol across sessions

**Observations**
- baseline shift
- feature distribution changes

**Expected system behavior**
- system should not assume cross-session consistency
- calibration or normalization required

**Design implication**
- per-session adaptation is mandatory
- stored models must not be blindly reused

---

## Experiment group B — IMU robustness

### B1. IMU stability during controlled motion

**Hypothesis**  
IMU provides stable kinematic information under clean motion but drifts over time.

**Setup**
- IMU-only mode
- no EMG influence

**Procedure**
- slow flexion
- holds at fixed angles
- repeated cycles

**Observations**
- angle estimates
- angular velocity
- drift over time

**Expected system behavior**
- smooth kinematic profiles
- drift visible during holds

**Design implication**
- IMU useful for motion context, not absolute truth
- periodic reset or fusion required

---

### B2. Motion artefacts

**Hypothesis**  
Sudden or unintended movements produce IMU artefacts that should not trigger assist.

**Setup**
- IMU-only
- sudden non-intentional motion

**Procedure**
- small bumps
- accidental arm movement

**Observations**
- spikes in acceleration/gyro

**Expected system behavior**
- artefact detection
- no assist triggered

**Design implication**
- IMU must be gated by context and quality checks

---

## Experiment group C — EMG + IMU fusion

### C1. Complementary signal degradation

**Hypothesis**  
Fusion of EMG and IMU improves confidence estimation when one signal degrades.

**Setup**
- EMG + IMU active
- assist disabled (observation mode)

**Procedure**
- intentionally degrade EMG (contact loss)
- keep IMU clean
- then reverse

**Observations**
- confidence scores
- system state transitions

**Expected system behavior**
- degraded confidence when one signal fails
- fallback when both fail

**Design implication**
- fusion improves *robustness*, not accuracy
- confidence gating is essential

---

### C2. Conflicting signals

**Hypothesis**  
EMG and IMU can disagree (muscle activation without motion, or motion without intent).

**Setup**
- EMG + IMU
- observation or low-assist mode

**Procedure**
- isometric contraction (EMG active, no motion)
- passive movement (motion without EMG)

**Observations**
- disagreement patterns

**Expected system behavior**
- no assist on conflict
- system prefers conservative state

**Design implication**
- assist requires agreement or high confidence
- disagreement reduces autonomy

---

## Experiment group D — Assist behavior & safety

### D1. Assist onset smoothness

**Hypothesis**  
Abrupt assist onset reduces trust and increases perceived risk.

**Setup**
- assist flexion enabled
- conservative limits

**Procedure**
- gradual activation
- repeated trials

**Observations**
- torque ramp
- user feedback (subjective notes)

**Expected system behavior**
- smooth assist onset
- no sudden force jumps

**Design implication**
- rate limiting is mandatory
- assist transitions must be gradual

---

### D2. Safety trigger validation

**Hypothesis**  
Safety triggers reliably override assist under abnormal conditions.

**Setup**
- assist enabled
- safety logging active

**Procedure**
- force joint limits
- introduce signal loss
- simulate latency spikes (if possible)

**Observations**
- state transitions
- actuator behavior
- logs

**Expected system behavior**
- immediate transition to Degraded / Fallback / Emergency
- assist disabled deterministically

**Design implication**
- safety layer is independent and authoritative

---

## Experiment group E — Human-in-the-loop behavior

### E1. User adaptation over time

**Hypothesis**  
User behavior adapts to system feedback and constraints.

**Setup**
- repeated sessions
- same user

**Procedure**
- observe muscle activation patterns over sessions
- note changes in timing and amplitude

**Observations**
- EMG patterns
- reduced false triggers (if any)

**Expected system behavior**
- improved interaction predictability
- no increase in assist aggressiveness

**Design implication**
- system design must expect co-adaptation
- static assumptions about user behavior are invalid

---

## Success criteria (MVP)

The experimental plan is successful if:

- failure modes are visible and reproducible
- safety mechanisms activate as designed
- uncertainty leads to conservative behavior
- meaningful conclusions can be drawn without ML

ML is considered beneficial only if it reduces unsafe assist events or increases confidence separation between valid and invalid signal states.
---

## Design reminder

> Experiments do not prove that the system is correct.  
> They prove that the system **fails in predictable and safe ways**.

That is the core goal of Reborn MVP.