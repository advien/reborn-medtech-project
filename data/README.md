# Data

No dataset files are committed to this repository — see `.gitignore` in this
directory. This file documents where to get the public datasets the notebooks
and `sim/` scripts expect, and how to lay them out locally.

## Datasets used

- **Ninapro** (https://ninapro.hevs.ch/) — multi-database sEMG + kinematics for
  hand/wrist/forearm movements. Used for intent classification (notebook 02)
  and drift/personalization (notebook 03).
- **EMG-EPN-612** (https://laboratorio-ia.epn.edu.ec/en/resources/dataset/emg-epn-612-dataset) —
  large-scale EMG gesture dataset, used as a cross-dataset check for drift
  experiments.
- **PhysioNet** (https://physionet.org/) — used opportunistically for
  additional EMG/IMU baselines where relevant.

## Layout convention

Downloaded datasets should be placed under `data/<dataset-name>/` (e.g.
`data/ninapro/`, `data/emg-epn-612/`) exactly as distributed by the source —
this repo does not re-host or re-package them. Notebooks and `sim/` scripts
reference these paths directly.

## Why data isn't committed

Per `docs/data-protocol.md`, the goal of data work here is validating system
behavior and signal reliability, not dataset accumulation — and public EMG/IMU
datasets are large and already versioned upstream. Committing them would bloat
the repo without adding reproducibility (the source datasets are the
canonical, citable version).
