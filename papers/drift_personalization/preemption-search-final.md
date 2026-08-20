# Final pre-emption search — Paper A novelty gate

*Adversarial search (2026-08-16) aimed at DISPROVING our novelty before manuscript
prep. Sources: web search over IEEE/PubMed/Semantic-Scholar/Scholar-indexed content,
+ one adjacent-field (EEG/BCI) pass. Verification: the only real EMG paper carrying
our exact table (Trifena 2025) was read in full (`related-work-calibration.md`);
confidence-rejection and general-ML anchors are classified from abstracts / known
canonical content. "Calibration" counted as **probability calibration** only when the
source clearly means confidence/ECE, not user/device recalibration.*

## Queries run
- Q1 `electromyography classifier miscalibration cross-session accuracy vs calibration temperature scaling` → only general-ML calibration papers; no EMG dissociation.
- Q3 `myoelectric confidence rejection threshold across days operating point false activations non-stationary EMG` → confidence-rejection line (within-session threshold selection); no session-transfer-of-operating-point study.
- BCI `EEG BCI confidence calibration cross-session ECE distribution shift` → cross-session variability heavy, but "calibration" = calibration-time; ECE not addressed.
- Benchmark `Ninapro expected calibration error reliability diagram sEMG` → NinaPro accuracy papers + generic ECE definitions; no cross-session ECE study on NinaPro.
- (Q2/Q4/Q5 covered within the above; no participant-level calibration-transfer,
  subject-heterogeneity-of-calibration, or binary-vs-multi-calibration EMG paper found.)

## 1. Q1–Q5 verdict table

| Q | Question | Credible direct pre-emption found? | Best hit | Verdict |
|---|---|---|---|---|
| Q1 | sEMG study explicitly characterizing cross-session **calibration vs performance** degradation | **No** | Trifena 2025 (weak venue, unremarked) | **SURVIVES** |
| Q2 | Credible study: good within-session calibration **does not transfer** cross-session, participant-level | **No** | Ovadia 2019 (general ML, not EMG, not participant-level) | **SURVIVES** |
| Q3 | Myoelectric study testing whether a **rejection/gate operating point** shifts its error-vs-availability across sessions | **No** | Scheme & Hudgins 2013 (within-session threshold only) | **SURVIVES** |
| Q4 | Per-subject **heterogeneity of calibration** degradation in sEMG | **No** | — | SURVIVES (thin) |
| Q5 | **Binary vs multi-class** compared on cross-session **calibration** | **No** | Trifena 2025 (multi worse, but accuracy-framed, not a calibration comparison) | SURVIVES |

No **credible peer-reviewed** direct pre-emption of Q1–Q5 was found.

## 2. Closest 5 prior papers

1. **Trifena tina (2025)** — *Real-Time Hand Gesture Recognition … Adaptive Prosthesis*,
   Elimensi J. Electrical Engineering 3(3), E-ISSN 2987-2928. **Read in full.**
   Dataset: **unnamed** (≥12 healthy + 3 amputees, 8–16 ch, 10–12 gestures). Sessions:
   within / cross-session / cross-subject. Metric: **ECE (1.8 / 3.6 / 5.9%)** +
   reliability diagram; also NLL mentioned. Level: **aggregate** (no per-subject).
   Gate-transfer tested: **No** (one in-session Hold/Limited/Full policy). Relevant
   content: reports accuracy+ECE across sessions and uses confidence-gated control, but
   reads ECE as *low = good* and never compares relative degradation. **PARTIAL
   OVERLAP** — the only real threat; mitigated by non-credible venue, no
   interpretation of the dissociation, no participant-level stats, no operating-point
   transfer.
2. **Scheme & Hudgins (2013)** — *Confidence-Based Rejection for Improved Pattern
   Recognition Myoelectric Control*, IEEE TBME, PMID 23322756 (DOI 10.1109/TBME.2012.2226175).
   Dataset: own PR data; able-bodied + amputee. Sessions: within. Task: myoelectric PR.
   Metric: classifier **confidence for rejection** (not ECE/calibration). Level:
   aggregate. Gate-transfer: No. Content: rejecting low-confidence decisions improves
   control. **BACKGROUND** (confidence *use*, not probability calibration).
3. **Robertson et al. (~2019)** — *Effects of Confidence-Based Rejection on Usability
   and Error in PR-Based Myoelectric Control*. Within-session; rejection thresholds
   0.60–0.75; usability trade-off. **BACKGROUND** (within-session operating point).
4. **Ovadia et al. (2019)** — *Can You Trust Your Model's Uncertainty?*, NeurIPS,
   arXiv:1906.02530. Non-EMG (image/text). Calibration degrades under dataset shift;
   temperature scaling fails under shift. **BACKGROUND** (general-ML precedent for the
   phenomenon; not sEMG, not participant-level, not gating).
5. **Guo et al. (2017)** — *On Calibration of Modern Neural Networks*, ICML,
   arXiv:1706.04599. Foundation of ECE / temperature scaling; modern nets overconfident.
   **BACKGROUND** (metric/method origin).

Also background: *A comparison of classification-based confidence metrics for
myoelectric control* (PubMed 26737972) — confidence-metric design, within-session.

## 3. Claims that SURVIVE unchanged
- The cross-session **calibration-vs-performance dissociation** is not characterized in
  any *credible* sEMG study (Q1).
- **Non-transfer** of within-session calibration to later sessions is not shown at the
  **participant level** in sEMG (Q2).
- **Session-transfer of a confidence/rejection operating point** is untested in
  myoelectric control (Q3) — the least-covered, most defensible niche.
- Per-subject **heterogeneity of calibration** degradation (Q4) and **binary-vs-multi
  calibration** comparison (Q5) are unreported.

## 4. Claims that MUST be weakened
- ❌ "First to observe calibration change across sEMG sessions" → **weaken**: Trifena's
  table already contains cross-session ECE. Say instead: *first **systematic,
  reproducible, participant-level, public-benchmark** characterization, and first to
  **name and quantify the dissociation** rather than report ECE as merely low.*
- ❌ "First ECE / first confidence-gating in EMG" → **drop entirely** (Trifena, Scheme &
  Hudgins).
- ❌ "Calibration degradation under shift is new" → **drop** (Ovadia/Guo).
- The **gate operating-point non-transfer** (Q3) may be stated as *not previously
  tested in myoelectric control* — the strongest genuine-novelty line — but keep
  "operational metric, not device safety."

## 5. Is the frozen primary framing still defensible?
**Yes, with the wording above.** The primary (systematic per-subject DB6
characterization, framed as *in-session calibration does not transfer*) is not
pre-empted by any credible source. The single real-EMG precedent (Trifena) is a weak
venue that reports-but-does-not-interpret and does no participant-level stats or
operating-point transfer — so our increment (credibility + interpretation + statistics
+ Q3 transfer test) stands, though it is **incremental, not first-of-kind**.

## 6. Recommendation
**GO (conditional conditions from `scope-gate.md` are met):** no credible
pre-emption of Q1–Q5. Proceed to the required experiments (subject-level stats;
NLL/Brier + robust ECE; minimal gate operating-point transfer), keeping the weakened
claims and disciplined terminology. Cite Trifena 2025 explicitly and differentiate;
anchor on Ovadia 2019 / Guo 2017. Lead genuine novelty with **Q3 (operating-point
non-transfer)** as the freshest line, supported by the Q1 dissociation.

*Stop. No new experiments proposed here.*
