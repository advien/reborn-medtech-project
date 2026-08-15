# EMG drift and few-shot personalization

**Phase B, topic 7** (docs/roadmap.md) — flagged as the strongest candidate
publication in the program. Cross-session/cross-subject EMG drift and few-shot
adaptation, built on `notebooks/02_intent_benchmark.ipynb` and
`notebooks/03_drift_fewshot.ipynb`, feeding `reborn.ml.personalization` once
trained.

The full plan — datasets and what each one controls for, the preprocessing
pipeline, the four evaluation protocols, the metrics, and the notebook →
artifact → paper map — is
[`docs/research/phase-b-plan.md`](../../docs/research/phase-b-plan.md). Two
things from it shape this manuscript:

- The paper carries a conventional accuracy baseline **and**, on top of it, what
  happens to *confidence calibration* under drift. The second is what connects
  phase B to the architecture paper: a model that loses accuracy while keeping
  confidence high opens the confidence gate and produces unexpected assistance,
  the worst failure mode in `docs/safety.md`.
- Reborn is an elbow orthosis; the datasets record the forearm. That domain gap
  belongs in the limitations section, and it keeps the claim about the method
  rather than about elbow physiology.

**Status: first results in.** Ninapro DB6 (s01, held-out s02) is downloaded and
the signal-quality / advisory-anomaly strand (the B3 line) is measured and written
up in [`findings-signal-quality.md`](findings-signal-quality.md) — including the
central drift result that a per-session adaptive threshold holds the advisory
false-positive rate at target across sessions without masking a genuinely degraded
one. The intent-classification baseline (B4) and cross-subject few-shot arm
(B6/B7) are not yet run. Once written, this paper should cite the specific code and
data git tag its figures were generated from.

Committed artifacts — the small aggregated tables behind the figures — go in
[`results/`](results/) here (with a provenance README); bulky per-window output
stays in the git-ignored `experiments/results/`.
