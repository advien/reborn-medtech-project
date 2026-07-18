# Reborn — Data Collection Protocol (MVP)

## Purpose of this document
This document defines **how and why data is collected** in the Reborn MVP.

The goal of data collection is **not dataset accumulation**, but:
- validation of system behavior
- evaluation of signal reliability
- understanding human–system interaction

All data collection is hypothesis-driven.

---

## General principles

1. **Data follows architecture**
   - What we collect is determined by system needs, not curiosity.

2. **Repeatability over volume**
   - Short, repeatable sessions are preferred to long recordings.

3. **Controlled degradation**
   - “Bad data” is intentionally collected to test failure handling.

4. **Human safety first**
   - Data collection must not require unsafe movements or loads.

---

## Signals and sampling

### EMG
- Raw EMG signal (per channel)
- Sampling rate: as supported by hardware (fixed per session)
- Metadata:
  - electrode placement (qualitative)
  - session ID
  - timestamp

### IMU
- Accelerometer
- Gyroscope
- Orientation estimate (if available)
- Metadata:
  - sensor placement
  - calibration status

### System-level signals
- system state (idle / assist / fallback / disabled)
- safety events
- latency markers (if available)

---

## Session structure (baseline)

Each session should be **short (5–15 minutes)** and structured.

### Session phases
1. **Rest / baseline**
   - relaxed arm
   - no intentional movement

2. **Intentional flexion**
   - slow flexion
   - medium-speed flexion
   - repeated flexion cycles

3. **Hold**
   - isometric contraction
   - partial flexion hold

4. **Rest**
   - recovery

All phases are **manually annotated** (coarse labels are enough).

---

## Experimental stages

### Stage 1 — EMG-only

**Goal:**  
Evaluate EMG stability and quality under controlled conditions.

**Collected data:**
- raw EMG
- EMG quality flags
- manual phase labels

**Scenarios:**
- clean electrode placement
- repeated sessions on different days
- intentional low activation vs high activation

**Expected outcomes:**
- visible intra-session variance
- noticeable inter-session drift
- identifiable “invalid signal” patterns

---

### Stage 2 — IMU-only

**Goal:**  
Establish kinematic baseline independent of muscle signal.

**Collected data:**
- joint angle proxy
- angular velocity
- IMU quality indicators

**Scenarios:**
- slow vs fast movement
- pauses and holds
- accidental motion artefacts

**Expected outcomes:**
- more stable temporal signal
- drift over time
- mismatch between motion and intention

---

### Stage 3 — EMG + IMU (Fusion)

**Goal:**  
Assess whether fusion improves **confidence**, not raw accuracy.

**Collected data:**
- synchronized EMG + IMU
- confidence metrics (heuristic or ML-based)
- decision outcomes

**Scenarios:**
- EMG degraded, IMU clean
- IMU degraded, EMG clean
- both degraded

**Expected outcomes:**
- clearer separation between “uncertain” and “valid” states
- safer system behavior under ambiguity

---

## Negative and edge-case data (required)

The following data **must be collected intentionally**:

- poor electrode contact
- muscle fatigue
- slight sensor misplacement
- pauses mid-movement
- inconsistent user intent

Purpose:
> Validate that the system reduces assist or disengages instead of guessing.

---

## Labeling strategy

Labels are:
- coarse
- session-level or phase-level
- manually assigned

Examples:
- `rest`
- `flex_slow`
- `flex_fast`
- `hold`
- `invalid_contact`

High label precision is **not required** at this stage.

---

## Data storage & structure

Each session is stored independently.

Example structure:
```text
session_YYYYMMDD_HHMM/
 ├── emg_raw.csv
 ├── imu_raw.csv
 ├── system_log.csv
 ├── labels.csv
 └── meta.json
