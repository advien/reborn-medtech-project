# Deferred notebooks — motion sensing and multimodal evidence

The two notebooks in this directory are **deferred, not abandoned**. They hold research
questions from the original phase-B plan that the current public track cannot answer, because
the repository has no dataset with synchronised motion (IMU) data alongside EMG and no IMU
loader in `reborn/data/loaders/`. Neither notebook contains code or results; each is its
question and a pointer to where that question is recorded.

| notebook | question |
|---|---|
| `04_imu_baselines.ipynb` | When does observed motion disagree with human intent? |
| `05_fusion_confidence.ipynb` | Does EMG + IMU fusion improve confidence estimation rather than prediction accuracy? |

The public evidence track today is the three-notebook progression in the parent directory:

    01_signal_trust  →  02_confidence_under_shift  →  03_when_not_to_help

Motion sensing, signal agreement/disagreement and multimodal fusion belong to a later Reborn
experimental phase — after the current offline, EMG-only evidence chain — together with the
closed-loop simulation and hardware work described in `docs/roadmap.md`. They are not part of
Public ML Track v1 and no dataset has been sought for them yet. The system architecture in
`docs/architecture.md` still describes EMG + IMU sensing; that is the intended future system,
and it is unchanged by the notebook track's scope.

See `docs/research/research-context.md` §4 for the questions in context.
