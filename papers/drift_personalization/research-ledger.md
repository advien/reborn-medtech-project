# Research ledger — Paper A

*Working framing: **Confidence Calibration Under Cross-Session sEMG Drift in
Myoelectric Intent Decoding.** Methodological, offline, NinaPro DB6 (intact
participants). No clinical / rehabilitation / prosthetic / human-factors claims.
"Unsafe-assist" is an operational offline metric defined by the existing decision
logic (`reborn.decision.confidence_gate`), NOT evidence of real-world harm.*

*This ledger is updated in place as evidence changes; outdated conclusions are
revised, not preserved. Numbers trace to `results/fulldb6_*.csv` and
`experiments/full_db6_calibration.py`, config fingerprint `fed1e81a523e5d6e`.*

---

## Milestone — PRIORITY 0: full DB6 (n = 10) validation _(2026-08-16)_

Extended the exact existing pipeline (frozen config, 2-channel montage, QC-gated
windowing, repetition-aware within-session + time-ordered cross-session splits,
ConfidenceGate metrics) from n=2 (s01–s02) to all 10 subjects, one subject at a
time. Balanced accuracy, ECE, unsafe-assist, availability, QC — per subject and
aggregated, for {binary, multi} × {LDA, logistic}.

### Central finding: calibration deteriorates more (relatively) than performance

**Evidence** (binary rest-vs-movement, the usable task; mean over 10 subjects ± sd):

| model | bal.acc within→cross | Δacc | ECE within→cross | ECE ratio | ECE worse in |
|---|---|---|---|---|---|
| LDA | 0.852 → 0.780 | −0.072 ± 0.052 | 0.028 → 0.051 | ×2.01 ± 0.88 | 8/10 (≥1.5× in 6/10) |
| logistic | 0.879 → 0.814 | −0.065 ± 0.048 | 0.028 → 0.060 | ×2.48 ± 1.50 | 10/10 (≥1.5× in 7/10) |

Balanced accuracy retains ~92% of its within-session value; ECE roughly **doubles**.
Unsafe-assist at the default gate rises 0.059 → 0.095 (LDA) / 0.046 → 0.076
(logistic); availability ~0.92 → 0.89. Multi-class: accuracy 0.414 → 0.250
(−40%), ECE ×3.35 (LDA) / ×5.17 (logistic).

**Interpretation.** Under cross-session drift a still-usable binary classifier
loses a modest amount of accuracy while its confidence becomes disproportionately
untrustworthy — ECE degrades ~an order of magnitude more in relative terms than
accuracy does. This is the failure mode a confidence-gated decoder is exposed to:
the gate consumes confidence, and confidence decays faster than the underlying
competence. The effect is present in the majority of subjects (ECE worse in
8–10/10) but heterogeneous (per-subject ECE ratio 0.89–3.65).

**Limit.** (1) The clean dissociation is a *binary-task* result; for multi-class
both accuracy and calibration collapse, so it is not "calibration alone." (2)
n=10, one dataset, one montage, two low-capacity models, offline. (3) Aggregate
gate behaviour is reported; the full threshold-sweep safety analysis is Priority 1.
(4) Not a claim about real devices or users.

**Clinical relevance.** For myoelectric intent decoding with a confidence gate,
model confidence is a safety-relevant signal, and this shows it degrades faster
and less visibly than accuracy under the routine, unavoidable condition of
recording on a different day. That is a concrete, overlooked reliability caveat
for confidence-gated decoding — stated at the method level, without clinical
extrapolation.

### What changed from n=2

The n=2 pilot (s01–s02) **understated** the effect: those two subjects are among
the cleaner, lower-drift ones (QC 0.67% / 0.10%; binary Δacc ~0.02). The full
sample shows larger and more heterogeneous drift. Specifically, the n=2 sub-claim
that *binary accuracy barely drifts* does **not** survive.

---

## Claims table

| Claim | Evidence | n | Robustness | Status |
|---|---|--:|---|---|
| Cross-session drift raises ECE substantially more (relative) than it lowers balanced accuracy (binary) | ECE ×2.0–2.5 vs acc −7–9% rel | 10 | ECE worse 8–10/10; per-subj ratio 0.89–3.65 | **CONFIRMED** |
| Binary intent decoding is more drift-robust than 8-class gesture ID | Δacc 0.072 vs 0.164; ECE ×2 vs ×3–5 | 10 | consistent across subjects | **CONFIRMED** |
| Binary accuracy is *nearly* drift-immune (n=2 impression) | n=2 Δacc 0.021 → n=10 0.072; per-subj 0.00–0.16 | 10 | fails | **REJECTED** |
| Multi-class calibration collapses under drift | ECE ×3.35 / ×5.17; acc −40% | 10 | 10/10 | **CONFIRMED** (both acc & ECE collapse) |
| Calibration drift worsens confidence-gate behaviour (unsafe-assist ↑) | unsafe 0.059→0.095 at default gate (binary/LDA) | 10 | aggregate only | **TENTATIVE** → Priority 1 |
| Degradation is episodic / concentrated in particular sessions | n=2: one session (s02/d02_t02); not yet re-tested | 2 | — | **TENTATIVE** → Priority 2 |
| QC rejection is subject-dependent | mean 1.06%, range 0.10%–6.55% (s06 highest) | 10 | wide spread | **CONFIRMED** (descriptive) |

---

## Superseded / to-rescope (flagged, not yet edited)

The earlier n=2 write-ups carry conclusions and framing now out of scope and
must be revised before the paper, not preserved:
- `findings-intent-drift.md` G1 (binary "barely drifts") — **rejected** above.
- `synthesis-two-monitors.md` and the architecture/two-monitor framing — rehab/
  orthosis-flavoured and beyond the methodological scope; hold for now.
- `findings-signal-quality.md` — the advisory-anomaly / adaptive-threshold line is
  not part of the calibration story; keep as separate material.

## Next (await go-ahead — do not auto-proceed)

- **Priority 1:** complete the gate-threshold sweep (unsafe-assist ↔ availability ↔
  threshold, within vs cross) on full DB6 — connect calibration drift to gate
  behaviour, terminology-disciplined.
- **Priority 2:** heterogeneity — gradual vs episodic vs subject-dependent; whether
  QC abnormalities (e.g. s06 6.55%) co-occur with calibration/accuracy loss; revisit
  the `sessions_elapsed = 3` case in the full sample. No causal claims.
- **Priority 3:** binary vs multi-class robustness on full data (above; CONFIRMED).
- **Priority 4:** few-shot recalibration — only if recovery headroom is informative.
