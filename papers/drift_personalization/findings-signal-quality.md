# Findings — signal quality and advisory anomaly detection under session drift

*Consolidated results of the B3 line (B3 → B3a → B3b → B3c → B3c-impl). Paper-ready
prose feeding the drift/personalization manuscript; a companion to `draft.md`.
Every number here traces to a committed artifact in [`results/`](results/) and to a
notebook run at config fingerprint `fed1e81a523e5d6e`. Status of each step is in
[`../../docs/research/checklist.md`](../../docs/research/checklist.md); the reasoning
chain is in [`../../docs/research/lab-notebook.md`](../../docs/research/lab-notebook.md).*

No claim of novelty is made here; that is deferred to the phase-A review
(`docs/research/research-context.md` §6–7). The contribution below is stated as
*evidence for design choices*, not as a new algorithm.

---

## 1. Scope and question

Before an assistive controller acts on an EMG window, the system must decide
whether that window can be trusted. Reborn separates this into two layers: a
**deterministic quality gate** the safety path relies on, and an **advisory
anomaly detector** that flags "this does not look like normal EMG" without a
per-mode rule. The B3 line asks, on real data: are these two layers correctly
calibrated, what do they actually catch, and how does **session drift** — the
central phenomenon of this paper — affect them?

**Data.** Ninapro DB6, subject s01, all ten sessions (five days × two sessions);
subject s02 held out. Two-channel montage (raw columns 0 and 10), chosen to mirror
Reborn's own hardware rather than a fourteen-electrode forearm array. Preprocessing:
2 kHz → 1 kHz, 20–450 Hz band-pass, 50 Hz notch, 200 ms / 50 ms windows, pure-label
windows only. 136 234 QC-assessed windows for s01.

## 2. Method summary

- **Deterministic QC** (`reborn.sensing.emg_qc`): dropout, saturation, clipping,
  amplitude-range, baseline-offset, mains checks. Thresholds are **derived from the
  data**, not chosen (`reborn.data.qc_calibration`), because the checks are
  absolute and DB6 samples are of order 1e-5 V.
- **Advisory detector** (`reborn.ml.anomaly.AnomalyDetector`): a one-class
  Mahalanobis model on a **fault-sensitive** feature set (`anomaly_features`:
  Hudgins time-domain + spectral + impulse). Output is advisory, consumed through
  the confidence gate, never overriding safety.
- **Fault injection** (`reborn.sensing.corruption`): dataset-scaled, for measuring
  detector sensitivity — not a source of results.

## 3. Findings

**F1 — QC thresholds must be data-derived; defaults measure units, not quality.**
The absolute default thresholds reject ~100% of DB6 for reasons unrelated to signal
quality. With data-derived thresholds, s01 rejects **0.67%** of windows, and the
thresholds transfer to held-out s02 (**0.10%**) — so they describe the dataset, not
one subject. Every rejection is `dropout`; the amplitude, offset, clipping and
saturation checks never fire on real DB6.
*Artifact:* `results/nb01_qc_rejection_*.csv`, `experiments/configs/ninapro_db6_qc.json`.

**F2 — Signal quality is episodic, not stationary.** Per-session rejection has
median 0.26% but session `d04_t01` rejects **3.57%** (13.5× the median), and its
same-day pair `d04_t02` is second-worst at 1.41% — a contact problem that persisted
across both sessions of day 4. A single global QC budget is therefore the wrong
abstraction; the system needs to notice a session degrading relative to the
wearer's own baseline. This requirement belongs to the safety layer, not the ML.
*Artifact:* `results/nb01_qc_rejection_*.csv`.

**F3 — Fault-detection rates are meaningless unless the injection is
dataset-scaled.** At severity scaled to DB6, the deterministic layer catches
dropout, saturation, clipping and baseline_offset **100%**, and `noise_burst`
**0%** (delegated to the advisory layer by design). With absolute default
amplitudes the same checks read saturation 18% and noise_burst 100% — artefacts of
injecting a fault ~50 000× the signal.
*Artifact:* `results/nb01_fault_detection_*.csv`.

**F4 — Amplitude features cannot separate a transient from a contraction; fault
detection has an energy floor.** On three amplitude features (RMS/MAV/ZCR) the
advisory detector flagged `noise_burst` at **2.8%** — below its own clean rate —
because in amplitude terms a burst looks like muscle activation. Adding spectral
(mean frequency, high-frequency power ratio) and impulse (kurtosis, crest factor,
sub-window RMS) features lifts saturation and clipping to **100%** and noise_burst
to **17%** at severity 3. Detection is a function of burst *energy* (amplitude ×
duration): ~8% at severity 1, ~19% at 3, **95% at severity 5, 100% by severity 8**.
A short, low-energy transient stays inside the natural window-to-window variation of
real EMG — a limit of window-level detection that no feature choice removes.
*Artifact:* `results/nb01_anomaly_*.csv`, `results/nb01_noise_burst_sweep_*.csv`.

**F5 — A high-dimensional one-class threshold must be calibrated out-of-sample.**
Ten features estimated from ~250 windows over-fit their covariance; a threshold read
off that same set runs the clean false-positive rate to **8.8%** against a 2.5%
target. Setting the threshold on a **separate held-out clean split** brings it to
**5.0%** (time-ordered) and **2.8%** (shuffled) — at target once the confound below
is removed.
*Artifact:* `results/nb01_fp_calibration_*.csv`.

**F6 — The residual false-positive gap is within-/between-session drift.** The
5.0%-vs-2.8% split isolates the cause: a threshold set on an earlier segment
under-covers a later one because the clean signal itself moves. Across s01's ten
sessions, a single fixed threshold gives benign false-positive rates spanning
**2.1%–12.5%** (mean 5.3%); a **per-session adaptive** threshold — recalibrated on
each session's own early clean windows, model fit held fixed — holds them at
**mean 2.6%, max 4.3%**. This is the drift this paper studies, surfacing in the
safety layer.
*Artifact:* `results/nb03_adaptive_threshold_*.csv`.

**F7 — Adaptation lowers false alarms without masking genuine degradation — but
only because it sits above a fixed floor.** The degraded session `d04` stays
elevated under adaptation (4.8% → **4.2%**, above the benign mean), because its
degradation is heterogeneous within the session and recalibrating on early clean
windows cannot normalise it away. Critically, this is safe only because adaptation
applies to the **advisory** threshold while the **deterministic** gate — which
independently caught d04's 488 dropout windows — remains a fixed, non-adaptive
floor. A single adaptive threshold with no floor would eventually mask a slow
*uniform* degradation. This is direct evidence for the "safety authoritative, ML
advisory" separation in `docs/safety.md`.
*Artifact:* `results/nb03_adaptive_threshold_*.csv`; policy in
`reborn.ml.anomaly.AdaptiveThreshold`.

## 4. What the B3 line establishes for the paper

1. A reproducible, data-derived QC calibration for open EMG datasets, with rejection
   rates that transfer across subjects (F1).
2. Evidence that signal quality is episodic (F2) and that the advisory detector's
   operating point drifts across sessions (F6) — both arguing for session-adaptive,
   not fixed, thresholds.
3. A measured account of *what each layer can and cannot catch*: named hard faults
   deterministically; broadband transients only above an energy floor (F3–F4).
4. An architectural result: advisory adaptation above a fixed deterministic floor
   reduces drift-driven false alarms **without** masking genuine degradation (F7).
   This is the concrete link from phase B to the architecture paper.

## 5. Limitations (declared, for the manuscript)

- **One subject for most results** (s01; s02 only as a held-out transfer check),
  **one dataset** (DB6), **two channels**. The cross-session numbers are within a
  single subject — cross-subject drift (few-shot) is B6/B7 and not yet measured.
- **Domain gap:** DB6 records the forearm; Reborn is an elbow orthosis. Claims are
  about the method, not elbow physiology.
- **Fault injection is synthetic** (scaled to real amplitudes). It measures detector
  sensitivity, not the prevalence of faults in real recordings.
- **Window-granularity floor** on brief transients (F4) is a property of the
  approach, not a tuning issue.
- **putEMG replication** (different hardware) is required before calling the
  deterministic checks *well-sized* rather than merely *inactive* on clean lab data.

## 6. Open questions → next

- Cross-subject drift and few-shot personalization (B6/B7): does per-subject
  adaptation behave like the per-session result here?
- Runtime integration: wire `AdaptiveThreshold` behind the deterministic floor into
  the control loop (phase C).
- Confidence calibration under drift (the paper's second axis, `README.md`): does a
  drifting detector keep confidence high while accuracy falls — the failure mode the
  confidence gate exists to prevent?
