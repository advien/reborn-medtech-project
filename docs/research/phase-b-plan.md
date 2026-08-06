# Phase B — open-data plan: datasets, processing, evaluation, write-up

**Status:** plan (§§1–9), plus a **findings** section (§0) recording what the first real DB6
runs changed. The plan below §0 is left as it was written *before* the data, so the
pre-registered design and what the data did to it stay separable; §0 is the only part that
post-dates results. Companion to [`docs/roadmap.md`](../roadmap.md) phase B and to
[`papers/drift_personalization/`](../../papers/drift_personalization/).

This document covers **public datasets used for research** (notebooks 01–05). It does not
replace [`docs/data-protocol.md`](../data-protocol.md), which governs data recorded from
Reborn's own hardware in the later engineering stage. The two are separate concerns: this one is
offline and read-only, that one is a collection protocol.

> **Integrity note**, mirroring the phase-A protocol: no result, rate, or figure is written into
> this repository until the pipeline below has actually produced it from downloaded data.
> Notebook 01's synthetic fixture is plumbing, not a result, and is labelled as such in the
> notebook. Per [`research-context.md`](research-context.md) §6–7 no novelty is assumed here
> either; what phase A finds may reframe this plan.

---

## 0. Findings that reframe the plan (2026-08-06, after notebooks 01–02 on DB6 s01–s02)

Everything below §0 was written before any data. This section records what the first real runs
(Ninapro DB6, subjects s01–s02, all 10 sessions, 2-channel montage, config `fed1e81a523e5d6e`)
established, and how notebooks 03–05 change as a result. The numbers live in the notebooks'
"Notes from this run" cells; this is the design consequence, not the table.

**F1 — The paper's thesis holds, and is measurable: calibration degrades faster than accuracy.**
Across every protocol/model run, cross-session ECE roughly doubles-to-triples while balanced
accuracy falls only a few points. A model that stays about as accurate but becomes much more
confident is one that opens the confidence gate on predictions it should refuse — exactly the
unexpected-assistance failure of `docs/safety.md`. This is the B→D bridge, now with evidence.

**F2 — The drift is episodic, not gradual.** Cross-session degradation does **not** grow with
elapsed sessions; it is flat except for one anomalous session (`sessions_elapsed = 3`) where
accuracy collapses and ECE/unsafe-assist spike. Notebook 01 reached the same shape from the QC
side: rejection is ~0.26% median with one session at 3.6%. **Two independent routes to one
conclusion** — the system's problem is *event detection* (this session is anomalous relative to
the wearer's baseline), not slow drift. This **changes notebook 03's framing**: few-shot
personalization on a fixed schedule addresses a drift shape the data does not show.

**F3 — Reborn's own task (binary rest-vs-movement) barely drifts; multi-class gesture ID drifts
a lot.** Binary loses ~0.02 balanced accuracy cross-session, multi-class ~0.10. The energy
decision survives an electrode being re-placed the next day; gesture identity does not. So the
drift *threat to Reborn specifically* is milder than the gesture-recognition literature implies,
and the paper must say so rather than borrow that literature's alarm.

**F4 — Cross-subject is not the worst case for the binary task** (it matches or beats
cross-session). For a binary energy decision, another person's data generalises about as well as
the same person on another day. So few-shot personalization has **much less headroom on the
binary task than the roadmap assumed** — notebook 03 must test that headroom exists before
optimising against it, rather than presupposing it.

**F5 — The advisory anomaly detector does not cover its one delegated mode.** `noise_burst` flags
at 2.8% vs a 4.4% clean rate; amplitude features (RMS/MAV/ZCR) cannot separate interference from
muscle activation, and refitting on rest-only windows does not fix it. **Consequence:** either add
a frequency-domain feature (band-power; EMG concentrates 20–150 Hz, broadband noise does not) or
state honestly that the mode is uncovered and falls to the IMU cross-check in notebook 05. The
two-layer coverage claim cannot stand unamended.

**F6 — Two channels cap multi-class, not binary.** ~0.47 balanced accuracy over 8 classes is a
montage limit (two electrodes cannot separate seven grasps), not a modelling one. Binary
conclusions are unaffected; multi-class numbers are a floor and must never be compared to
14-channel literature.

### What this does to the downstream notebooks

- **Notebook 03** is reframed from "slow drift + few-shot" to **"episodic degradation +
  gate-threshold sweep"**: how far does unsafe-assist move as the gate threshold sweeps, and does
  few-shot calibration restore *calibration* faster than *accuracy*? The binary task is primary;
  cross-subject headroom is tested, not assumed (F3, F4). Investigating the one anomalous session
  directly is worth more than another model (F2).
- **Notebook 01** gains a band-power feature before **notebook 05** may assume fusion covers
  `noise_burst` (F5).
- **The paper's central table** is the ECE-vs-accuracy divergence across protocols (F1), with the
  binary/multi-class split (F3) as the framing that makes it Reborn's result rather than a generic
  one.

The stop rule (`docs/research/checklist.md`) did **not** fire — there is a real, measurable
cross-session effect — but its spirit did: the effect is not the *gradual* drift the roadmap
imagined, so the framing moved to match the data rather than the data being forced to the framing.

---

## 1. What phase B is for

Phase B has to answer one question that the rest of Reborn depends on:

> When sEMG drifts across sessions, what happens to the **confidence estimate** that
> `reborn.decision.confidence_gate` consumes?

The failure that matters to a safety-first system is not "accuracy dropped". It is "accuracy
dropped **while confidence stayed high**" — because that is the case where the gate opens and the
system delivers assistance the user did not ask for. `docs/safety.md` and
[`research-context.md`](research-context.md) §5.3 name unexpected assistance as the worst failure
mode; this is the phase that measures whether the ML layer can produce it.

So the paper carries two things: a conventional cross-session/cross-subject accuracy baseline (so
the numbers are comparable to the literature), and, built on top of it, the calibration and
downstream-safety analysis (which is what connects phase B to phase D).

## 2. Decisions taken

| Decision | Choice | Why |
|---|---|---|
| Sequencing | Phase B data layer starts now; phase A search runs alongside | Phase B is blocked only by a missing loader; the two need different kinds of attention and do not compete |
| Contribution framing | Accuracy baseline **and** calibration/unsafe-assist, one paper | Baseline alone is a crowded field; calibration alone is hard to situate without the baseline |
| First dataset | Ninapro DB6, subject subset first | See §3 — DB6 is the only candidate where *session* is a cleanly controlled factor |

## 3. Datasets — each one is a different controlled variable

The datasets are **not interchangeable batches**. Each isolates one factor, and the evaluation
protocol in §6 depends on that. This is the reason the loader is an interface (§4) rather than a
script per dataset.

| Dataset | Controlled variable it isolates | Specification |
|---|---|---|
| **Ninapro DB6** | **Session / day** — same subjects, same protocol, repeated | 10 intact subjects, 14 Delsys Trigno double-differential electrodes on the forearm, 2 kHz, 7 ADL grasps × 12 repetitions, 2 sessions per day × 5 days = 10 sessions per subject. Built specifically to study repeatability |
| **EMG-EPN-612** | **Subject** — many users, few repetitions each | 612 users, Myo armband (8 channels), 5 gestures + rest, ~50 repetitions per subject, JSON |
| **putEMG** | **Independent replication** of the drift result on different hardware | 44 subjects, 24 channels, 5120 Hz, 8 gestures, two recordings separated by ≥1 week, HDF5. CC BY-NC 4.0 — research use only, note the licence in the paper |
| HD-sEMG isometric elbow | **Anatomy** — external-validity check only | Small; used in the limitations section, not for the main claim |

**Order of acquisition.** DB6 for 2–3 subjects → build and freeze the pipeline → DB6 in full →
EPN-612 for the few-shot arm → putEMG for replication. Do not download everything up front: the
pipeline design is what needs settling, and it settles fastest against the smallest dataset that
still contains the factor of interest.

### The domain gap, stated up front

Reborn is an **elbow** orthosis with a binary flex / no-flex intent. Every dataset above except
the last records the **forearm** during hand and wrist gestures. This is a real gap and it goes in
the paper's limitations, not in a footnote. Two consequences for how the work is framed:

- The claim is about the **method** — how cross-session drift affects confidence calibration in
  sEMG intent decoding — not about elbow-specific physiology.
- Where the task must be binary to mirror Reborn, it is derived honestly: *rest* vs *any
  non-rest gesture*, with the multi-class result reported alongside so the reduction is visible.

## 4. Data layout and the loader interface

Raw datasets are never committed (`data/.gitignore`). Layout follows `data/README.md`:

```
data/
  ninapro_db6/      # as distributed by the source, unmodified
  emg_epn_612/
  putemg/
  cache/            # preprocessed windows (.npz) + manifest.json
```

`reborn/data/` holds the loading layer. It is **research-side and offline** — it is not part of the
runtime control loop and must not be imported by `reborn/decision/`, `reborn/safety/`, or
`reborn/control/`. It depends on `reborn.sensing` and nothing else in the package. Each dataset
gets a backend that returns the same canonical `EmgRecording`, so protocols, metrics, and
notebooks are written once.

A later phase-C bridge — replaying an `EmgRecording` through a `SensorSource` so recorded EMG
drives the simulation loop, per `docs/roadmap.md` — is deliberately *not* built here. The record
type is shaped so it stays easy.

## 5. Processing pipeline

The governing rule: **the notebook calls `reborn.sensing`; it does not carry its own
preprocessing.** If the notebook filters differently from the runtime, the paper measures a system
that does not exist.

1. **Load** → canonical `EmgRecording(signal[n_samples, n_channels], sample_rate, labels,
   subject_id, session_id, trial_id)`.
2. **Resample** all datasets to a common 1 kHz. Their native rates differ by more than an order of
   magnitude (200 Hz Myo to 5120 Hz putEMG); comparing feature statistics across them is only
   meaningful at a common rate.
3. **Filter** — band-pass 20–450 Hz, notch 50 Hz, via `reborn.sensing.filters`.
4. **Window** — 200 ms windows, 50 ms stride. Each window is labelled by the label at its **last
   sample**, so the window is causal and contains no information from after the decision instant.
   This is the single most common source of inflated numbers in this literature.
5. **QC gate before ML** — `reborn.sensing.emg_qc.assess_quality_report` runs on every window.
   Windows that fail are excluded from the ML set *and counted*. The rejection rate per session is
   itself a reported result: it is what the safety layer would have done at runtime, and a
   pipeline that silently keeps unusable windows measures something the deployed system would
   never see.
6. **Features** — `reborn.sensing.features`, the full Hudgins time-domain set (RMS, MAV, ZCR,
   waveform length, slope-sign changes; batched over a `WindowSet` by `reborn.data.features`).
   Standardised on **training statistics only** — pooling the scaler over train and test leaks the
   per-session amplitude shift that *is* the drift under study. CPU only, no GPU dependency.
   Per §0/F5, a frequency-domain (band-power) feature is still to be added for the `noise_burst`
   coverage gap.
7. **Cache** — preprocessed windows to `data/cache/*.npz` with a `manifest.json` recording the
   hash of the preprocessing configuration, so a figure in the paper names the exact configuration
   that produced it.

Models: LDA and calibrated logistic regression first. A small 1D CNN only if the simple models
are demonstrably the limiting factor — the question here is about confidence behaviour, and a
model whose calibration can be reasoned about is worth more than a point of accuracy.

## 6. Evaluation protocols

Splits are by **session** and by **subject**. Never random-shuffle at window level: adjacent
windows overlap by 150 ms, so a random split puts near-copies of the same window on both sides and
the result is meaningless.

| Protocol | Train | Test | What it measures |
|---|---|---|---|
| Within-session | earlier repetitions of session *k* | later repetitions of session *k* | Ceiling |
| **Cross-session** | sessions 1..k | session k+1.. | **Drift — the core result** |
| Cross-subject | subjects A | subjects B | Worst case, no calibration |
| Random-shuffle | — | — | Reported **once**, as a control (see note below) |

> **Correction from the first runs (see §0):** the within-session split must be **by repetition**,
> not by time. Ninapro is block-designed — every repetition of one grasp is recorded before the
> next grasp begins — so a temporal cut puts whole classes on one side of the train/test line and
> produces a "ceiling" that sits *below* cross-session. `within_session_splits` splits by
> repetition when the loader supplies repetition numbers and falls back to a self-flagging temporal
> split otherwise. And the random-shuffle inflation is **model-capacity-dependent**: LDA on ten
> features showed none, so the row is a control on the *protocol-and-model pair*, not a fixed
> correction factor — it must be re-run before any higher-capacity model is trusted.

Few-shot personalization is evaluated on top of cross-session and cross-subject: *n* calibration
**repetitions** from the target session, *n* ∈ {1, 2, 4, 8} (`add_calibration_repetitions` —
whole repetitions, the unit a user actually performs), with the question posed as "how many
repetitions restore safe behaviour", not "how many add accuracy". Per §0/F4, whether the binary
task has headroom for this at all is itself a question, not an assumption.

## 7. Metrics

- **Accuracy / balanced accuracy, per protocol** — the comparable baseline.
- **Calibration**: expected calibration error and reliability diagrams, per protocol. The
  interesting quantity is how ECE moves between within-session and cross-session, not its
  absolute value.
- **Unsafe-assist rate** — fraction of windows where the confidence gate would have permitted
  assist while the true label is *no intent*. Computed by running predictions through the actual
  `reborn.decision.confidence_gate`, not a reimplementation of it.
- **QC rejection rate**, per session (from step 5).

Sweeping the gate threshold gives an unsafe-assist / assist-availability curve — the honest way to
present the trade-off, and the figure the architecture paper will reuse.

## 8. Notebooks → artifacts → paper

A notebook does not *hold* a result; it **produces an artifact**. Figures are rendered by a
separate script from a CSV, never inline from a live kernel — otherwise no number in the paper can
be traced back, which is the same contract phase A makes for its search log.

Two destinations, because `experiments/results/` is git-ignored in full:

- **Raw and bulky output** (per-window predictions, sweep logs) → `experiments/results/`, ignored.
- **The small aggregated tables that appear in the paper** → `papers/drift_personalization/results/`,
  committed, alongside the figure scripts that consume them. This mirrors how
  `papers/review_adherence/` commits its screening and extraction CSVs.

| Notebook | Produces | Paper section |
|---|---|---|
| `01_emg_qc_and_baselines` | QC rejection rates and detector performance on real windows | Signal quality and what the safety layer rejects |
| `02_intent_benchmark` | Accuracy across all four protocols, binary + multi-class | Baseline; the binary/multi drift split (F3) |
| `03_drift_fewshot` | ECE, reliability curves, gate-threshold sweep, few-shot repetition sweep | Core result — calibration-vs-accuracy divergence (F1) |
| `04_imu_baselines`, `05_fusion_confidence` | — | Out of scope for this paper; likely the next one |

Draft location: `papers/drift_personalization/`. The manuscript cites the git tag of the code and
the cache manifest its figures came from.

## 9. Execution order

1. ✅ `reborn/data/` — records, loader interface, synthetic backend, DB6 backend, pipeline, splits, tests.
2. ✅ Download DB6 (s01–s02); QC thresholds calibrated from data → `experiments/configs/ninapro_db6_qc.json`.
3. ✅ Notebook 01 on real windows → QC rejection rates + fault/anomaly detection (see §0/F5).
4. ✅ Notebook 02 → four-protocol baseline, all four runs (see §0/F1–F4, F6).
5. ⏳ **Notebook 03 — reframed per §0** → gate-threshold sweep (unsafe-assist vs availability),
   ECE-vs-accuracy divergence under episodic degradation, the anomalous `sessions_elapsed = 3`
   session investigated directly. Binary task primary.
6. ⏳ Notebook 03 → few-shot **repetition** sweep, *after* confirming there is headroom to recover
   (F4). Add a band-power feature (F5) around here or in 01.
7. ⏳ Draft `papers/drift_personalization/` from committed result tables; add DB6 remaining subjects,
   putEMG replication, and EPN-612 few-shot as the external-validity arms.

## 10. Environment

Bare `python` on the development machine resolves to the Windows Store alias and the `pip` on PATH
belongs to a 3.14 interpreter that has only numpy. The working interpreter is **3.11**, which has
numpy, scipy and pytest and matches the byte-code already in the tree; reach it as `py -3.11`.

Still outstanding for the ML arm: `pip install -e ".[dev,ml]"` under 3.11 (scikit-learn is not
installed yet) and `h5py` for putEMG. Ninapro `.mat` files need only `scipy.io`, already present.
Pinning phase B to a dedicated virtual environment would be worth doing before the first result,
so the figures name an environment that can be recreated.
