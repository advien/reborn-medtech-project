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

## Deep-dive 2026-08-16 — the elimensi paper read in full (verdict revised)

**Trifena tina (2025), "Real-Time Hand Gesture Recognition from EMG Biosignals
Using Interpretable Deep Learning for Adaptive Prosthesis," Elimensi J. of
Electrical Engineering 3(3), E-ISSN 2987-2928.** Full text read (12 pp).

**It reports accuracy AND ECE across within / cross-session / cross-subject:**

| scenario | accuracy | macro-F1 | ECE |
|---|---|---|---|
| within-session | 96.8% | 96.1% | 1.8% |
| cross-session | 91.7% | 90.5% | 3.6% |
| cross-subject | 86.4% | 84.9% | 5.9% |

- **The dissociation is present in their own numbers** (computed by us): within→cross-
  session accuracy −5% but **ECE ×2.0**; within→cross-subject accuracy −11% but
  **ECE ×3.3** — the same pattern we measured on DB6 (ECE ~×2 cross-session). This
  **independently corroborates the phenomenon**.
- **But they do not notice or frame it.** They read ECE as *low = good* ("a low
  ECE indicates a well-calibrated probability for the reject/defer policy") and use
  it to justify confidence-gated control. They never compare the *relative*
  degradation of ECE vs accuracy; the asymmetry sits uninterpreted in the table.
- **Confidence-gated control from calibrated probabilities is explicitly their
  framing too** (Hold/Limited/Full on `max p(y|x)` thresholds) — so that angle is
  not unprecedented either.

**Quality caveats (weight this as weak prior art).** Obscure single-author venue;
gmail affiliation; vague/un-named dataset ("minimum 12 healthy + 3 amputees",
"8–16 channels", "10–12 gestures"); a garbled reference ([8] "Invitation, H.");
suspiciously clean figures. Reads as possibly AI-assisted / low-rigor. It would
likely be unknown to reviewers in this area, but it exists and shows the idea is "in the
air."

### Revised verdict (honest)
- **Phenomenon:** real and now *corroborated by an independent sEMG source* — good
  for validity, but it means the effect is **not unobserved** in sEMG.
- **ECE across sessions in sEMG + calibration→gating:** **not unprecedented**
  (this paper does both; Guo et al. 2017 is the ECE foundation; Gal & Ghahramani
  2016 MC-dropout). Our earlier "no one reports ECE cross-session in sEMG" is
  **too strong — retracted.**
- **Remaining defensible contribution is narrower and consolidation-type:** (a) a
  *systematic, reproducible, public-benchmark* quantification (NinaPro DB6, n=10,
  per-subject, both binary and multi-class, exact leakage controls) — versus
  single low-tier reports on private data; and (b) **explicitly naming and centring
  the dissociation** (calibration degrades disproportionately, so a *low in-session
  ECE does not license trust after a day*) that existing reports leave uninterpreted
  (they read ECE as "good"). This is legitimate for a short methodological paper but is
  **incremental, not a first-of-kind** — the framing must say so.

## Reference anchors (verified this session)
- Guo, Pleiss, Sun, Weinberger 2017, "On Calibration of Modern Neural Networks",
  ICML — the ECE / temperature-scaling foundation. *Verified (cited across sources).*
- Gal & Ghahramani 2016, "Dropout as a Bayesian Approximation", ICML — MC-dropout.
- Ovadia et al. 2019 (arXiv:1906.02530) — calibration degrades under dataset shift.
- Scheme & Hudgins — confidence-based rejection in myoelectric control.
- Trifena tina 2025 (above) — sEMG cross-session accuracy+ECE, gating; weak venue.

## Next (await go-ahead)
- Decide the angle given the revised verdict: (i) reframe as *systematic
  validation + naming the dissociation on a public benchmark* (honest, incremental,
  scope-appropriate); or (ii) pivot the contribution toward what is genuinely less
  covered — e.g. the **per-subject heterogeneity of the dissociation** and **whether
  low in-session ECE predicts post-drift trustworthiness** (a *warning* result), or
  the few-shot **calibration-vs-accuracy recovery** question (Priority 4).
- A confirmatory database search (Scopus/IEEE/S2) is still worth one pass to see how
  many *credible* venues report the accuracy-vs-ECE table across sessions.
