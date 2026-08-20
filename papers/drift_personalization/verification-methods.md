# Methods verification (source-of-truth) — probability, gate metric, ECE

*Verification only (2026-08-16). No code/pipeline changed. Traces the committed
implementation for the Methods section. Primary sources:
`experiments/full_db6_calibration.py`, `reborn/data/evaluation.py`,
`reborn/decision/confidence_gate.py`, `reborn/data/records.py`,
`reborn/data/features.py`; numbers from `results/fulldb6_aggregate.csv`.*

## 1. Probability pipeline

| Model | Fit | Probability source | Confidence definition | Post-hoc calibration | Manuscript name |
|---|---|---|---|---|---|
| LDA | `sklearn.discriminant_analysis.LinearDiscriminantAnalysis()` (defaults: svd solver, no shrinkage) fit on **train-standardised** features (`reborn.data.features.standardize`, train stats only) — `full_db6_calibration.py::make_fit_predict` | `model.predict_proba(X_test)` (LDA Gaussian posterior) | `max_k p(y=k\|x)` = `np.max(proba, axis=1)` | **NO** | Linear Discriminant Analysis (native posterior probabilities) |
| Logistic | `sklearn.linear_model.LogisticRegression(max_iter=2000)` (defaults: L2, lbfgs; binary→sigmoid, multi→softmax) same standardisation — `full_db6_calibration.py::make_fit_predict` (the `MODELS` dict; the line the writing track cited) | `model.predict_proba(X_test)` | `max_k p(y=k\|x)` = `np.max(proba, axis=1)` | **NO** | logistic regression (native probabilities) — **NOT** "calibrated logistic regression" |

**Post-hoc calibration search (whole repo, .py):** `CalibratedClassifierCV`, Platt/sigmoid,
isotonic, temperature scaling, `calibration_curve`, custom calibrators → **none found.**

> The study evaluates the **native** probability estimates of LDA and logistic
> regression; it does **not** apply any post-hoc probability calibration.

**Terminology verdict:** "calibrated logistic regression" is **INCORRECT** for both
models. Logistic regression producing probabilities is not "calibrated logistic
regression" (that term denotes a post-hoc-calibrated estimator, e.g.
`CalibratedClassifierCV`). Call it "logistic regression (native probabilities)".

## 2. Gate metric — what `unsafe_assist_rate` actually computes

- **Code location:** `reborn/data/evaluation.py::unsafe_assist_rate`; gate =
  `reborn/decision/confidence_gate.py::ConfidenceGate.evaluate`; invoked per split by
  `evaluate_split` with the **default** `ConfidenceGate()` = `low=0.4, high=0.7`.
- **Exact event (per window):** `assist_scale(conf) > 0` (gate permits) **AND**
  `ŷ ≠ REST_LABEL` (predicted movement) **AND** `y = REST_LABEL` (true rest).
  `REST_LABEL = 0`; binary labels = `(labels != 0)` so rest=0, movement=1.
- **Numerator:** `count(permit ∧ ŷ≠rest ∧ y=rest)`.
- **Denominator:** **all evaluated windows** (`np.mean` over the full test array) —
  **not** rest-only, not gate-eligible-only.
- **Mathematical definition:**
  `rate = (1/N) · Σ_i 1[ assist_scale(conf_i) > 0 ] · 1[ ŷ_i ≠ 0 ] · 1[ y_i = 0 ]`.
- **A. Physical assistance?** **NO.** Pure offline array computation; no hardware
  activated, no movement delivered, no user exposed.
- **B. "Permission"** = decision-layer output: `ConfidenceGate.evaluate(conf).assist_scale > 0`,
  i.e. confidence strictly above the low threshold (0.4). A simulated gate decision.
- **C. Necessarily a classification error?** **Yes** — the event requires `ŷ=movement`
  while `y=rest`, i.e. it is exactly a **false positive** (movement predicted during
  true rest) that the gate permitted.
- **D. Denominator population:** **all windows.**

**Critical caveat — the gate does not bind on the binary task.** Binary
`predict_proba` has two classes, so `conf = max` posterior is **always ≥ 0.5 > 0.4**
(the low threshold). Hence `assist_scale > 0` for **every** window, and on the binary
task the metric reduces to the **ungated** rest false-positive prevalence
`P(ŷ=movement ∧ y=rest)` over all windows. At the default threshold the "gate" is a
no-op for binary; the reported change reflects the classifier's false-positive rate,
not gate behaviour. (Same applies to `assist_availability`, whose denominator is
true-movement windows.)

- **Hardware/physical assistance involved:** **NO.**
- **Current `unsafe-assist` name accurate:** **NO.**

## 3. Terminology recommendation

| Candidate | Class | One-line reason |
|---|---|---|
| unsafe-assist rate | **MISLEADING** | Implies physical/safety harm; nothing is assisted, offline, and the gate is inactive on binary. |
| false assist-permission rate | **ACCEPTABLE WITH DEFINITION** | Captures permit∧false, but "assist/permission" implies the gate acts — it does not on binary at τ=0.4. |
| incorrect assist-permission rate | **ACCEPTABLE WITH DEFINITION** | Same as above. |
| false activation rate | **ACCEPTABLE WITH DEFINITION** | Matches myoelectric usage, but that convention is usually per-rest-window; here the denominator is **all** windows. |
| gate error rate | **INCORRECT** | Counts only one error type (FP-during-rest), and the gate does not bind on binary. |

**Recommended manuscript term:** none is an exact match. Use the literal description of
what is observed: **"rest-phase false-positive rate (per window, gate-permissive at
τ = 0.4)"** — i.e. the fraction of all windows in which the model predicts movement
during true rest and the confidence gate permits it. State the threshold and the
all-window denominator explicitly; note the gate is non-binding on the binary task at
τ = 0.4. If a real gate sweep with τ > 0.5 is added later, "false assist-permission
rate" becomes appropriate.

## 4. Existing 0.059 → 0.095 result

- **VERIFIED.** `results/fulldb6_aggregate.csv`, row `binary / lda`:
  `within_unsafe_mean = 0.05949`, `cross_unsafe_mean = 0.09540` (round to 0.059→0.095).
- **Exact meaning:** the §2 metric (rest-phase FP rate, per window) for the **binary
  LDA** model, within-session vs cross-session.
- **Threshold:** default `ConfidenceGate(low=0.4, high=0.7)` — **non-binding on binary**
  (see §2), so effectively the ungated rest-FP prevalence.
- **Model:** binary rest-vs-movement, LDA.
- **Aggregation:** per split → mean over a subject's within/cross splits
  (`summarize`) → **mean across the 10 subjects** (subject-level mean of split-level
  rates). Not a pooled-window rate.
- **Denominator:** all test windows within each split.
- (Logistic counterpart, same CSV: `0.0462 → 0.0756`.)

## 5. ECE verification

- **Implementation:** `reborn/data/evaluation.py::expected_calibration_error`.
- **Bins:** `n_bins = 10`, **equal-width** (`np.linspace(0, 1, 11)`); half-open bins,
  the last closed so `conf == 1.0` is counted.
- **Confidence:** top-label, `conf = max_k p(y=k|x)` (the same array as §1).
- **Correctness:** `1[y_true == y_pred]` (top-label correctness).
- **Weighting:** standard weighted ECE — each bin weighted by its share of samples
  (`weight = mean(in_bin)`); `ECE = Σ_bins weight · |acc_bin − mean_conf_bin|`.
- **Aggregation:** computed **per split** (in `evaluate_split`) → averaged over splits
  to a per-subject value (`summarize`) → averaged over subjects (`full_db6_calibration.py`).
  **Not pooled** across all windows/subjects.
- **n = 10 values verified: YES.** `fulldb6_aggregate.csv`: binary LDA
  `within_ece 0.02763 → cross_ece 0.05110` (= reported 0.028→0.051); binary logistic
  `0.02796 → 0.05991` (= reported 0.028→0.060).
- Known ECE caveats (equal-width binning sensitivity; not a proper scoring rule) are
  a manuscript limitation, not an implementation error.

## 6. Documentation conflicts (correction table — NOT yet edited)

| Location | Current statement | Implementation says | Required correction |
|---|---|---|---|
| `docs/research/phase-b-plan.md:192` | "calibrated logistic regression" | native `LogisticRegression`, no post-hoc calibration | "logistic regression (native probabilities)" |
| `notebooks/02_intent_benchmark.ipynb` (cell nb02-model-md) | "LDA and calibrated logistic regression" | same | remove "calibrated" |
| `papers/drift_personalization/draft.md:68` | "calibrated logistic regression" | same | remove "calibrated" *(user-owned draft — flag, do not auto-edit)* |
| Multiple (`research-ledger.md`, `findings-intent-drift.md`, `synthesis-two-monitors.md`, `checklist.md`, `lab-notebook.md`, notebook 03) | "unsafe-assist rate" | rest-phase FP rate, per window, gate non-binding on binary | rename to the §3 operational term + define |
| `findings-intent-drift.md` / notebook 03 (gate framing) | implies gate governs binary assist decisions | gate is non-binding on binary at τ=0.4 | state gate is inactive on binary at default τ; any gate claim needs τ>0.5 |

## 7. Writing-track handoff (paste-ready facts)

1. Both classifiers use scikit-learn native probabilities: `LinearDiscriminantAnalysis().predict_proba` and `LogisticRegression(max_iter=2000).predict_proba`. **No post-hoc calibration** (no temperature scaling, Platt, isotonic, or `CalibratedClassifierCV`) is applied anywhere.
2. The manuscript must **not** say "calibrated logistic regression"; say "logistic regression (native probability estimates)".
3. Confidence is the **top-label posterior**, `max_k p(y=k|x)`.
4. ECE is standard **10-bin equal-width** top-label weighted ECE, computed **per split, averaged per subject, then across subjects** (not pooled). Reported binary values: LDA 0.028→0.051, logistic 0.028→0.060 (within→cross) — verified against the committed CSV.
5. The "unsafe-assist" metric = per-window fraction where the gate permits AND the model predicts movement during true rest; denominator = **all windows**; it is a **classification false-positive** event, computed **offline**, with **no hardware/physical assistance**.
6. At the **default gate (0.4/0.7)** the binary confidence (always ≥0.5) means the gate **permits every window**, so on the binary task the metric is an **ungated rest false-positive prevalence**; the 0.059→0.095 change is a classifier-error change, not a gate effect.
7. Do not use clinical/safety wording for this metric; use e.g. "rest-phase false-positive rate (per window, τ=0.4)".
8. 0.059→0.095 is the binary-LDA within→cross value, **subject-level mean of split-level rates over 10 subjects** (default gate), verified in `fulldb6_aggregate.csv`.
9. Any claim about "confidence-gate behaviour" on the binary task requires re-running the gate with a threshold τ>0.5 (a required experiment already listed); the current numbers do not demonstrate gate mediation on binary.
10. All numbers trace to `experiments/full_db6_calibration.py` + `results/fulldb6_*.csv` at config fingerprint `fed1e81a523e5d6e`.
