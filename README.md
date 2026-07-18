# Reborn — Human-in-the-loop Assistive Robotics System

**Reborn** is a research and engineering program studying the **decision-making process of an
assistive robotic system under uncertainty**, using a safety-first, human-in-the-loop active
elbow orthosis as the concrete vehicle.

The central research question:

> **How should an assistive robotic system determine the appropriate level of assistance under
> uncertain sensing conditions?**

EMG, IMU, sensor fusion, ML, and the orthosis itself are *tools* here, not the research object —
see [`docs/research/research-context.md`](docs/research/research-context.md). The guiding design hypothesis:

> The primary objective of an assistive robotic system is not to maximize assistance.
> It is to maximize **appropriate** assistance.
>
> In assistive systems, the worst failure is not "no help" — it is **unexpected help**.

This repository holds two things side by side:

- **Research** (`notebooks/`, `papers/`) — open-data ML experiments and the papers built on top
  of them.
- **The Reborn system** (`reborn/`, `sim/`) — a Python package implementing the sensing →
  decision → actuation → safety control loop, runnable today in simulation and, later, on real
  hardware.

The system is built around a hardware abstraction layer (HAL): control, decision, and safety
code only ever talk to `SensorSource`/`ActuatorSink` interfaces, never to a specific backend. See
[`docs/architecture.md`](docs/architecture.md) for details — this is the central design decision
of the project.

## Repository layout

```text
reborn/
├── docs/           # architecture, safety, data protocol, experiment plan, roadmap
├── reborn/         # the Python package — hal/, sensing/, plant/, control/, decision/,
│                   # safety/, ml/, logging/
├── sim/            # runnable simulation experiments (entry points into the package)
├── notebooks/      # open-data ML exploration (phase B)
├── data/           # dataset pointers only — no data files committed
├── experiments/    # run configs and results
├── papers/         # one folder per publication, each citing a code/data git tag
├── firmware/       # hardware stage (not started)
├── assets/         # diagrams, photos, demo material
└── tests/          # unit tests — safety layer is not optional coverage
```

## Status

Engineering proceeds in two stages: **simulation first, then hardware.** Today, the HAL and the
`sim` backend are real and usable; `decision/`, `safety/`, and `logging/` have working minimal
implementations; `plant/`, `control/`, and `ml/` are skeletons awaiting phase C/B work. See
[`docs/roadmap.md`](docs/roadmap.md) for the full research plan and
[`sim/run_baseline_loop.py`](sim/run_baseline_loop.py) for the current minimal working loop.

## Getting started

```bash
pip install -e ".[dev]"
pytest
python sim/run_baseline_loop.py
```

## Key documents

- [`docs/research/research-context.md`](docs/research/research-context.md) — what Reborn actually studies, the
  research hypothesis, and the open questions to settle before claiming novelty
- [`docs/architecture.md`](docs/architecture.md) — layers, module boundaries, HAL
- [`docs/safety.md`](docs/safety.md) — safety philosophy, states, triggers, ML boundaries
- [`docs/data-protocol.md`](docs/data-protocol.md) — how data is collected and why
- [`docs/experiments.md`](docs/experiments.md) — hypothesis-driven validation plan
- [`docs/roadmap.md`](docs/roadmap.md) — research roadmap across phases A–D

## Explicitly out of scope

Medical certification or clinical claims, product-level mechanical design, and ML-driven
autonomous control are all intentionally excluded. This is a research and engineering case, not a
product or a clinical claim.

## Citing this work

See [`CITATION.cff`](CITATION.cff).
