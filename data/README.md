# Data

No dataset files are committed to this repository — see `.gitignore` in this
directory. This file documents where to get the public datasets the notebooks
and `sim/` scripts expect, and how to lay them out locally.

## Datasets used

Which dataset isolates which factor, and why each was chosen, is in
[`docs/research/phase-b-plan.md`](../docs/research/phase-b-plan.md) §3.

- **Ninapro DB6** (https://ninapro.hevs.ch/) — the primary cross-session set:
  10 subjects, 14 forearm electrodes at 2 kHz, 10 sessions across 5 days. Built
  for repeatability, so *session* is a cleanly controlled factor. Notebooks
  01–03.
- **EMG-EPN-612** (https://laboratorio-ia.epn.edu.ec/en/resources/dataset/emg-epn-612-dataset) —
  612 users on a Myo armband; the scale needed for the few-shot
  personalization arm, where *subject* is the varied factor.
- **putEMG** (https://biolab.put.poznan.pl/putemg-dataset/) — 44 subjects,
  24 channels, two sessions a week apart. Independent replication of the drift
  result on different hardware. CC BY-NC 4.0: research use only.
- **PhysioNet** (https://physionet.org/) — opportunistic, including the
  HD-sEMG elbow recordings used only as an external-validity check against the
  forearm-versus-elbow domain gap.

## Layout convention

Downloaded datasets go under `data/<dataset-name>/` exactly as distributed —
this repo does not re-host or re-package them:

```text
data/
  ninapro_db6/
  emg_epn_612/
  putemg/
  cache/        # preprocessed windows (.npz) + manifest.json, regenerable
```

Loading is not done ad hoc per notebook. `reborn/data/` holds one backend per
dataset, all returning the same `EmgRecording`, plus the preprocessing pipeline
and evaluation protocols; point a loader at the directory above:

```python
from reborn.data import PreprocessConfig, build_window_set
from reborn.data.loaders import NinaproDB6Loader

loader = NinaproDB6Loader("data/ninapro_db6")
windows = build_window_set(loader.load(subjects=["s01"]), PreprocessConfig())
```

`cache/` is regenerable output, not source data — deleting it costs only compute.

## Why data isn't committed

Per `docs/data-protocol.md`, the goal of data work here is validating system
behavior and signal reliability, not dataset accumulation — and public EMG/IMU
datasets are large and already versioned upstream. Committing them would bloat
the repo without adding reproducibility (the source datasets are the
canonical, citable version).
