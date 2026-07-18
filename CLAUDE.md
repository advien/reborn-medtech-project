# CLAUDE.md

Context for Claude Code sessions working in this repository. Read this first.

## What this project is

Reborn studies the **decision-making process of an assistive robotic system under uncertainty**,
using a safety-first, human-in-the-loop active elbow orthosis as the vehicle. EMG/IMU/fusion/ML
are tools, not the research object — the question is how a system should determine the
*appropriate* level of assistance when its own sensing is unreliable.

Two things live in this repo: research (`notebooks/`, `papers/`) and the Reborn system itself
(`reborn/` package, `sim/` entry points). Read
[`docs/research/research-context.md`](docs/research/research-context.md) for what the project is actually asking,
then [`docs/architecture.md`](docs/architecture.md) and [`docs/safety.md`](docs/safety.md) for
design intent — before making structural changes.

Note that per `docs/research/research-context.md`, no component of this project is assumed novel, and
novelty claims are explicitly deferred until the phase-A literature review answers what's already
solved. Don't write "novel"/"first"/"state-of-the-art" framing into docs or papers on your own
initiative.

## Invariants that must not be broken

1. **HAL is the spine.** Anything outside `reborn/hal/` (sensing, decision, safety, control, ml)
   must only depend on the `SensorSource`/`ActuatorSink` interfaces in
   `reborn/hal/interfaces.py`, never on `sim_backend` or `hardware_backend` directly. If you find
   yourself importing a backend from outside `hal/` or `sim/`, that's a design violation — stop
   and reconsider.
2. **Safety is authoritative and ML is not.** `reborn/safety/` can override any other component.
   `reborn/ml/` outputs are advisory only — bounded, optional, and never wired directly to
   actuator commands. Confidence gating (`reborn/decision/confidence_gate.py`) sits between ML
   and decision logic; low confidence must reduce assist, never increase it.
3. **Uncertainty reduces autonomy.** When signal quality or confidence is low, the system does
   *less*, not more. This shapes `decision/state_machine.py` and `safety/fallback.py`.
4. **Safety code is tested code.** Any change to `reborn/safety/` or `reborn/decision/` needs
   corresponding coverage in `tests/`. This is treated as part of the scientific claim, not
   boilerplate.

## Current implementation depth (as of this rebuild)

- `reborn/hal/` — fully implemented (interfaces + sim backend). `hardware_backend.py` is an
  intentional stub for the later hardware stage.
- `reborn/decision/`, `reborn/safety/`, `reborn/logging/`, `reborn/sensing/` — real, minimal,
  tested implementations.
- `reborn/plant/`, `reborn/control/` — skeletons with TODOs; phase C (simulation control work)
  hasn't started yet per `docs/roadmap.md`.
- `reborn/ml/` — interface stubs; phase B (open-data ML) training work hasn't produced models to
  wire in yet.

Don't quietly upgrade a skeleton into a full implementation as a side effect of an unrelated
task — that's a scoped decision the user makes deliberately, tied to which roadmap phase is
active.

## Dev workflow

```bash
pip install -e ".[dev]"
pytest                          # safety/decision layer coverage
python sim/run_baseline_loop.py # minimal end-to-end loop (sim backend)
```

## Data

No dataset files are committed (`data/.gitignore`). `data/README.md` documents which public
datasets (Ninapro, EMG-EPN-612, PhysioNet) the notebooks and `sim/` scripts expect, and where to
download them locally.

## Papers

Each folder under `papers/` corresponds to one roadmap phase/topic and should cite the specific
code and data git tag its figures were generated from — see `docs/roadmap.md` for the phase map.
