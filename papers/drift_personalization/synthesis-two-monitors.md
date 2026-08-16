# Synthesis — two monitors, two failure modes

*The conclusion the B3 and B4 lines build to, and the empirical result phase B hands
to the architecture / position paper. Grounded in
[`findings-signal-quality.md`](findings-signal-quality.md) (F1–F7),
[`findings-intent-drift.md`](findings-intent-drift.md) (G1–G8), and the CSVs in
[`results/`](results/). Ninapro DB6, subjects s01–s02, config fingerprint
`fed1e81a523e5d6e`. No novelty claimed (deferred to the phase-A review).*

---

## The claim

A safety-first assistive system that acts on a learned intent signal needs **two
independent drift monitors, not one**: a monitor of the **input** (is the signal
trustworthy?) and a monitor of the **decision** (does the learned mapping still
apply?). Neither subsumes the other, and DB6 exhibits a distinct failure mode for
each that its counterpart is blind to.

## The evidence — one dataset, two failure modes

| | `d04` (subject s01) | `d02_t02` (subject s02) |
|---|---|---|
| What happened | Electrode contact fault (F2) | Concept drift — rest/movement boundary moved (G7) |
| Input monitor (QC + anomaly, models of P(x)) | **Caught** — QC rejects 3.6% dropout; the deterministic floor fires | **Blind** — anomaly flag rate its *lowest* (0.5% ch0) |
| Classifier accuracy | Fine (0.92 balanced) — no decision signal | **Collapses** (0.641 balanced, ECE 0.187) |
| Decision monitor (confidence dist. + model disagreement, behaviour of P(y\|x)) | Quiet — nothing to flag | **Caught** — confidence 0.79 vs ~0.93; disagreement 22% vs ~5% |

The two failure modes sit on opposite diagonals: the input monitor catches the one
the decision monitor misses, and vice versa. A system with only one of them ships a
blind spot with real safety cost — `d02_t02` produces overconfident wrong assist
(ECE 0.187, unsafe-assist ~0.05) that no input check would stop.

## Why the per-window confidence gate is not enough

Reborn already has a confidence gate, and it consumes the classifier's per-window
confidence. On `d02_t02` that is insufficient: the mean confidence drops only to
0.79 and individual wrong windows remain high-confidence, so a per-window threshold
still opens on them (that is what the 0.187 ECE *is*). What flags the session is the
**distributional** view — mean confidence, and especially **model disagreement**,
which needs no labels and separates `d02_t02` from every other session by ~4×. The
decision monitor is therefore a *session-level* signal that gates or recalibrates,
sitting beside — not inside — the per-window confidence gate.

## Mapping onto the Reborn architecture

- **Input monitor** = `reborn.sensing.emg_qc` (deterministic floor, F1) + the
  advisory `reborn.ml.anomaly` detector with its per-session `AdaptiveThreshold`
  (B3c). Authoritative floor + adaptive advisor, already implemented and tested.
- **Decision monitor** = a new, still-unbuilt component watching the classifier's
  confidence distribution and cross-model disagreement over a session. It belongs in
  `reborn.decision` beside `confidence_gate`, is label-free, and would lower assist
  (or trigger few-shot recalibration) when it fires.
- Both feed the safety layer; **uncertainty from either reduces autonomy**
  (`docs/safety.md`). This is the same invariant, now shown to require two sensors of
  uncertainty, not one.

## Limitations

- Each failure mode rests on a **single session** (s01/d04, s02/d02_t02), two
  subjects, one dataset (DB6), a two-channel montage. The claim is a demonstrated
  *existence* of the two-monitor gap, not its frequency. putEMG / EMG-EPN-612
  replication (B9) is needed before any prevalence statement.
- The decision monitor is so far a *diagnostic* (notebook 03), not a wired component;
  a threshold, warm-up, and false-alarm budget for it are unquantified.
- Model disagreement used LDA vs logistic regression — two low-capacity models. Its
  behaviour with a higher-capacity pair is untested.

## What this hands forward

- **Architecture / position paper:** the concrete, measured basis for a two-monitor
  safety architecture — input-quality and decision-drift as separate, non-redundant
  layers feeding the gate. (See `papers/architecture_position/`.)
- **Notebook 03 next:** does few-shot recalibration on a handful of labelled windows
  restore the boundary on `d02_t02` (fix concept drift) — and does it restore
  *calibration* faster than *accuracy* (G2)? That closes phase B's personalization
  arm (B6/B7) and tests whether the decision monitor should *gate* or *trigger
  recalibration*.
