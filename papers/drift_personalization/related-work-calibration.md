# Related work — is the calibration-vs-performance claim novel?

*Targeted literature probe (abstract-level) for the central claim:*

> Under cross-session sEMG drift, confidence **calibration** deteriorates
> substantially more than **classification performance** — a reliability failure
> mode for confidence-gated myoelectric intent decoding.

*Searched 2026-08-16 via web search + abstract reads. This is a scoping probe, not
a systematic review; it records verified pointers and an honest novelty verdict.
Only papers actually found are listed; author/year left `TBD` where not yet
confirmed from the source. Full-text verification of the starred items is the
recommended next step before locking the framing.*

---

## What the search establishes

### 1. In general ML, the phenomenon is well-known — not novel
- **Ovadia et al., 2019 — "Can You Trust Your Model's Uncertainty? Evaluating
  Predictive Uncertainty Under Dataset Shift"** (NeurIPS; arXiv:1906.02530; ~1300+
  citations). *Verified.* The canonical result: predictive-uncertainty/calibration
  quality **degrades under dataset shift**, and post-hoc calibration (temperature
  scaling) fitted in-distribution **fails** under shift. The general framing "a
  reliable model should keep low calibration error even as accuracy degrades under
  shift" is explicitly discussed in this line.
- **Implication:** the *phenomenon* (calibration degrades under distribution/session
  shift, sometimes more visibly than accuracy) is established in ML. A reviewer will
  know this. Our contribution cannot be "we discovered this"; it must be
  domain-specific measurement + the confidence-gating consequence.

### 2. In sEMG / myoelectric control, confidence is used — but for rejection, not calibration
- **Scheme, Hudgins et al. — "Confidence-Based Rejection for Improved Pattern
  Recognition Myoelectric Control"** (IEEE TBME; Semantic Scholar). *Verified title.*
- **"A comparison of classification based confidence metrics for use in the design
  of myoelectric control systems"** (PubMed 26737972). *Verified.*
- **"CNN Confidence Estimation for Rejection-Based Hand Gesture Classification in
  Myoelectric Control"** (IEEE THMS; White Rose eprints). *Verified title.*
- **Reading:** this established line **uses** confidence to *reject* uncertain
  decisions and compares confidence *metrics*, but does **not** characterise whether
  confidence is **calibrated**, nor how calibration behaves across sessions. Closest
  prior art, but a different question (use vs. reliability of confidence).

### 3. Cross-session/cross-day drift is heavily studied — but reported in accuracy/F1
- Cross-day HD-sEMG (arXiv:2309.12602 ViT-MDHGR): accuracy only, **no ECE/calibration**
  cross-day (confirmed via abstract fetch). *Verified.*
- Multistream deep sEMG (PMC13075277): single-session, **no ECE**; but explicitly
  flags that CE-trained nets are "poorly calibrated ... overconfident ... concerning
  in safety-critical systems like EMG-controlled prostheses." *Verified* — motivation
  stated, not measured across sessions.
- Dominant response to drift is domain adaptation / transfer learning / retraining to
  **restore accuracy**.

### 4. "Calibration" is an overloaded term in EMG — mostly means *retraining burden*
- e.g. "Robust myoelectric pattern recognition methods for reducing users'
  **calibration** burden" (PMC10839078). Here *calibration* = the user recalibration/
  training session, **not** probability calibration (ECE). *Verified.* This overloading
  is itself part of why probability calibration is under-measured in the field.

### 5. ECE is *emerging* in EMG/gesture work, but as a method target, not a drift diagnosis
- **UAC — "Uncertainty-Aware Calibration of Neural Networks for Gesture Detection"**
  (arXiv:2504.02895): calibrates IMU-gesture probabilities; finds existing methods
  (temperature scaling, entropy max, Laplace) don't calibrate these models well.
  *Verified via full fetch.* Method paper; does **not** report a cross-session
  accuracy-vs-calibration dissociation.
- At least one cross-session EMG framework reports both accuracy and ECE (search
  snippet: "cross-session ~91.7%, ECE ≈ 3.6%"). *Unverified source (star: confirm).*
  Reports ECE as an outcome; not framed as the dissociation.
- \* Real-time EMG hand-gesture paper (cdfpublisher/elimensi #412) surfaced as using
  ECE; **could not verify** (HTTP 403). Needs a full-text check.

---

## Honest novelty verdict

- **The phenomenon is NOT novel in ML** (Ovadia 2019 and successors).
- **In myoelectric control specifically**, the search found: confidence used for
  *rejection*; cross-session drift measured in *accuracy/F1*; "calibration" mostly
  meaning *retraining*; ECE only *emerging* (2023–2026) and as a *method target*. I
  found **no sEMG paper that quantifies and frames the cross-session
  accuracy-vs-calibration dissociation** as a reliability failure mode for
  confidence-**gated** decoding.
- **So the defensible contribution is domain-specific and framing-level**, not a new
  phenomenon: *bring a known-in-ML effect into cross-session sEMG intent decoding,
  measure it (ECE ~doubles while accuracy holds ~92%, n=10 DB6), and connect it to
  confidence-gate behaviour* — in a subfield that largely reports accuracy, uses
  confidence for rejection, and says "calibration" to mean retraining.

## Risks / how to not overclaim
1. **Positioning must credit Ovadia-style ML precedent** and claim only the sEMG-
   specific measurement + gating consequence. Not "first to observe."
2. **A direct pre-emption may exist** in a 2024–2026 sEMG paper the abstract-level
   search missed. Before locking the framing, run a confirmatory search (Scopus / IEEE
   Xplore / Semantic Scholar API) on `(EMG OR electromyography) AND ("calibration" OR
   "expected calibration error" OR "reliability diagram") AND (session OR day OR
   cross-day)` and pull full text of the 3–4 closest hits.
3. Keep terminology disciplined: **probability calibration / ECE**, explicitly
   distinguished from **user recalibration**.

## Next (await go-ahead)
- Confirmatory search on the databases above; full-text of: the cross-session-ECE
  framework, the elimensi real-time paper (\*), UAC, and 1–2 confidence-rejection
  papers — to be certain no one states the dissociation.
- If clear: write the positioning paragraph (precedent → gap → this paper's
  measurement + gating consequence).
