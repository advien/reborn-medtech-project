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

Not started. The data layer (`reborn/data/`) exists and is tested against a
synthetic fixture; no dataset has been downloaded and no result exists. Once
written, this paper should cite the specific code and data git tag its figures
were generated from.

Committed artifacts — the small aggregated tables behind the figures — go in
`results/` here; bulky per-window output stays in the git-ignored
`experiments/results/`.
