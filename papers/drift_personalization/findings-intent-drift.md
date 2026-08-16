# Findings — intent classification and confidence calibration under session drift

*Consolidated results of B4 (notebook 02, intent benchmark). Paper-ready prose,
companion to [`findings-signal-quality.md`](findings-signal-quality.md) (the B3
line) and `draft.md`. Numbers trace to `results/nb02_*.csv` at config fingerprint
`fed1e81a523e5d6e`; the notebook's §8 carries the same analysis inline. No novelty
is claimed (deferred to the phase-A review).*

---

## 1. Scope and question

The drift paper needs a comparable accuracy baseline, and — more importantly for
Reborn — an answer to what happens to **confidence** under drift, since a model
that stays confident while losing accuracy opens the confidence gate on
predictions it should refuse (`docs/safety.md`). B4 scores intent classification
on Ninapro DB6 (s01–s02, all ten sessions, 259 745 windows, two-channel montage,
QC-rejected 0.40%) under **four protocols** — within-session (ceiling),
cross-session (drift), cross-subject (worst case), random-shuffle (control) — for
two tasks (binary rest-vs-movement, multi-class 8-way) and two models (LDA,
logistic regression). Standardisation is fit on training rows only, so the
per-session amplitude shift under study does not leak.

## 2. The stop-rule verdict

The checklist stop rule: *if cross-session is indistinguishable from within-session
across the full range, there is no drift and the paper must be reframed before
continuing.* **It does not fire — but it reshapes the story.** Drift is present
(most clearly in calibration and in the multi-class task), so the paper stands; but
for the binary task Reborn actually makes, the drift is **small in accuracy and
episodic rather than gradual**. Notebook 03's framing should therefore be *episodic
degradation / event detection*, not slow cumulative drift.

## 3. Findings

Balanced accuracy, within-session → cross-session (`results/nb02_summary_*.csv`):

| protocol | binary/lda | binary/logreg | multi/lda | multi/logreg |
|---|---|---|---|---|
| within-session | 0.917 | 0.949 | 0.468 | 0.477 |
| cross-session | 0.896 | 0.929 | 0.359 | 0.376 |
| cross-subject | 0.912 | 0.945 | 0.273 | 0.284 |
| random-shuffle | 0.901 | 0.951 | 0.343 | 0.361 |

**G1 — The binary task barely drifts; the multi-class task drifts a lot.** Binary
loses 0.021 (LDA) / 0.020 (logreg) balanced accuracy across sessions; multi-class
loses **0.109 / 0.102**. Rest-vs-movement is close to a decision on signal energy,
and energy survives an electrode being replaced the next day; *which* gesture is
made does not. Reborn's decision is the binary one, so the drift threat to *this*
system is milder than the gesture-recognition literature implies — the paper should
say so rather than borrow that literature's alarm.

**G2 — Calibration degrades faster than accuracy. (The architecture link.)** Across
sessions ECE roughly **doubles to triples** in every run — binary 0.016→0.027 (LDA),
0.012→0.028 (logreg); multi 0.065→0.164, 0.030→0.109 — while accuracy falls by a
few points at most. The model does not become much worse; it becomes **more sure
than it deserves to be**, which is precisely the condition under which the
confidence gate opens on predictions it should refuse. This is the finding that
connects phase B to the architecture paper.

**G3 — The drift is episodic, not cumulative** (`results/nb02_splits_binary_lda_*.csv`,
§6). Degradation does not grow with elapsed sessions: binary-LDA balanced accuracy
by sessions-elapsed reads 0.906, 0.924, **0.756**, 0.932, 0.918, 0.926, 0.886,
0.909, 0.909. One session (`sessions_elapsed = 3`) collapses — ECE 0.097 (~5× its
neighbours), unsafe-assist 0.048 (~3×) — and the rest sit flat. A personalization
strategy that recalibrates on a fixed schedule addresses a drift shape this dataset
does not show; what the data asks for is *event detection* — the same requirement
notebook 01 reached from the QC side (F2). **Two independent routes, one
conclusion.**

**G4 — Cross-subject is not the worst case for the binary task.** It scores 0.912 /
0.945 — matching or beating cross-session. For a binary energy decision another
person's data generalises as well as the same person's on another day; for
multi-class it behaves as expected (0.273 / 0.284, clearly worst). Few-shot
personalization therefore has much less headroom on the binary task than the
roadmap assumed, and notebook 03 should test that assumption before optimising
against it.

**G5 — The random-shuffle control shows no inflation, as the model predicts.**
+0.005 over cross-session (binary LDA), and negative for multi-class: LDA on ten
features has nothing to memorise from the 150 ms-overlapping near-duplicates. The
control row stays and must be re-run before any higher-capacity model is trusted.

**G6 — Two channels cap the multi-class task.** 0.47 balanced accuracy over eight
classes (chance 0.125) is well above chance but poor in absolute terms — a montage
limit, not a modelling failure. It does not touch the binary conclusions Reborn
needs, and multi-class numbers here are a floor, never to be compared against
14-channel literature.

**G7 — The cross-session collapse is concept drift, invisible to the input
monitors (B4a).** The whole cross-session degradation is *one* split — subject s02
tested on `d02_t02` (train `d01_t01`), balanced accuracy 0.641, ECE 0.187 — and it
is **not** the QC-degraded session (s01/`d04` classifies fine, G3/F2). The advisory
anomaly detector, fit on the train session, does not single it out: its channel-0
flag rate is the *lowest* of all s02 sessions (0.5%) and channel-1 mid-pack (6.4%),
while sessions that classify perfectly (`d05_t01`, 11.8%) look *more* anomalous.
Yet on `d02_t02` both classes' recall falls (rest 0.70, movement 0.58) at barely
reduced confidence (0.79 vs ~0.93) — the input looks normal while the learned
rest/movement boundary has moved. This is **concept drift** (P(y|x)), which QC and
a one-class anomaly detector (both models of P(x)) are blind to by construction.
**Safety implication:** signal-quality/anomaly monitoring (the B3 layers) and
decision-level drift monitoring are *distinct* requirements; the confidence gate
consumes the classifier's own confidence, which does not collapse here, so it cannot
rescue the case. Preventing overconfident wrong assist under concept drift needs a
monitor of the *decision* — the classifier's confidence distribution over time,
cross-channel/model disagreement, or periodic few-shot recalibration — not more
input monitoring.
*Artifact:* `results/nb03_b4a_concept_drift_*.csv`; reproduced in notebook 03 (B4a).

## 4. Methodological correction (recorded for the manuscript)

The within-session protocol originally split **temporally**, which is wrong for
Ninapro: DB6 records all twelve repetitions of one grasp contiguously, so a 70/30
temporal cut left classes untrained and untested and put the "ceiling" *below*
cross-session. `within_session_splits` now splits **by repetition** (the Ninapro
convention) when repetition numbers are present; the multi-class ceiling moved to
0.468 and behaves like one. The temporal path remains as a self-flagging fallback.

## 5. Limitations

- Two subjects (s01–s02), one dataset (DB6), two channels; cross-subject rests on
  two subjects only. LDA / logistic regression, not a high-capacity model — a CNN
  is warranted only if these prove limiting, which G1–G2 suggest they are not for
  the binary task.
- Forearm data, elbow target: the domain gap keeps claims about the method, not
  physiology.
- The episodic collapse rests on a single session (`sessions_elapsed = 3`);
  naming what happened in it (next step) matters more than another model.

## 6. Open questions → next

1. ~~Investigate `sessions_elapsed = 3`~~ — **done (G7)**: it is concept drift on
   s02/`d02_t02`, invisible to the input monitors. The follow-up it raises is a
   *decision-level* drift monitor (confidence-distribution / disagreement), which the
   B3 input layers do not provide.
2. **Notebook 03**: given ECE doubles while accuracy holds (G2) and a decision-level
   monitor is now motivated (G7), how far does the unsafe-assist rate move as the
   gate threshold sweeps, and does few-shot calibration restore *calibration* faster
   than *accuracy*?
3. Cross-subject few-shot headroom is smaller than assumed for the binary task
   (G4) — test before optimising.
