# EMG cross-session drift and confidence calibration for a safety-first assistive orthosis

**Draft manuscript — Phase B, topic 7.** Companion to
[`docs/research/phase-b-plan.md`](../../docs/research/phase-b-plan.md) (design + findings §0) and
[`README.md`](README.md). Target venue: arXiv preprint → workshop at ICRA / IROS / EMBC
(`docs/roadmap.md`).

> **Status: skeleton with real content where the pipeline has already produced it.**
> Intro, Data & Methods, Limitations, and the qualitative Findings (F1–F6, from notebooks 01–02 on
> real Ninapro DB6) are written. Every **number, table, and figure is a `PENDING` marker** naming the
> committed CSV / notebook that will produce it — per the integrity note in `phase-b-plan.md`, no
> figure is typed into the manuscript before its artifact exists in `results/`. Per
> `docs/research/research-context.md` §6–7, no novelty is claimed; that framing waits on phase A.

---

## Abstract

`TBD — written last, once the notebook 03 results table exists.` One paragraph: cross-session sEMG
drift degrades *confidence calibration* faster than it degrades *accuracy*; for a safety-first
assist decision this is the failure that matters, because a still-accurate but over-confident model
opens the confidence gate on predictions it should refuse. Reports the ECE-vs-accuracy divergence
across four protocols on Ninapro DB6, the binary-vs-multiclass split, and how many calibration
repetitions restore *safe* behaviour.

## 1. Introduction

Assistive orthoses that decode intent from sEMG are usually optimised for classification accuracy.
For a *safety-first* system the relevant quantity is different: not "is the prediction right" but
"does the system know when its prediction is unreliable enough to withhold assistance". The worst
failure mode of an active elbow orthosis is not *no assistance* but *unexpected assistance* — the
gate opening on a false intent (`docs/safety.md`, `research-context.md` §3, §5.3).

This paper measures what cross-session drift does to the **confidence estimate** that
`reborn.decision.confidence_gate` consumes. Contribution is two layers, one paper:

1. a conventional cross-session / cross-subject accuracy baseline (comparable to the literature);
2. built on it, the **calibration and downstream-safety** analysis — how expected calibration error
   and the *unsafe-assist rate* move under drift. Layer 2 is the bridge to the architecture paper
   (phase D): it supplies empirical evidence that the ML layer can produce the exact failure the
   safety architecture is designed to contain.

`Related work — TBD, seeded by phase A's literature map (papers/review_adherence). Sketch: sEMG
cross-session/cross-subject degradation; few-shot / calibration-based personalization; confidence
calibration (ECE, temperature scaling); assist-as-needed. No "novel/first" until phase A answers.`

## 2. Data and methods

Fully specified (pre-registered) in `phase-b-plan.md` §§3–7; summarised here.

**Datasets — each isolates one controlled variable.** Ninapro DB6 (session/day — the core drift
factor; 10 subjects, forearm, repeated over 10 sessions) is primary. EMG-EPN-612 (subject) supplies
the few-shot arm; putEMG (independent hardware) is the replication check. Runs to date use DB6
subjects s01–s02, 2-channel montage, config `fed1e81a523e5d6e`.

**Domain gap, stated up front.** Reborn is an *elbow* orthosis with binary flex/no-flex intent;
these datasets record the *forearm* during hand/wrist gestures. The claim is therefore about the
**method** (how drift affects calibration in sEMG intent decoding), not elbow physiology. Where the
task must mirror Reborn it is derived honestly as *rest* vs *any non-rest*, reported alongside the
multi-class result. This is a limitation, not a footnote (§6).

**Pipeline** (`reborn.sensing`, so the paper measures the deployed system): canonical
`EmgRecording` → resample 1 kHz → band-pass 20–450 Hz + 50 Hz notch → 200 ms / 50 ms causal windows
labelled at the last sample → **QC gate before ML** (rejected windows excluded *and counted* — the
rejection rate is itself a reported result) → Hudgins time-domain features, scaler on **training
statistics only** (pooling would leak the per-session amplitude shift that *is* the drift) → cached
with a config-hash manifest. `A band-power (frequency-domain) feature is still to be added — see
F5.` Models: LDA and calibrated logistic regression first; a 1D CNN only if the simple models are
demonstrably the limiting factor.

**Evaluation protocols** (split by session and by subject — never window-level shuffle; adjacent
windows overlap 150 ms):

| Protocol | Measures |
|---|---|
| Within-session (split **by repetition**, not time — DB6 is block-designed) | ceiling |
| **Cross-session** | **drift — the core result** |
| Cross-subject | worst case, no calibration |
| Random-shuffle | reported once, as a model-dependent control |

**Metrics.** Balanced accuracy; expected calibration error + reliability diagrams; **unsafe-assist
rate** (fraction of windows where the *actual* `reborn.decision.confidence_gate` would permit assist
while the true label is *no intent*); QC rejection rate per session. Sweeping the gate threshold
gives the unsafe-assist / assist-availability curve reused by the architecture paper.

## 3. Results

> All tables/figures below are `PENDING` their committed artifact in
> `papers/drift_personalization/results/*.csv` (produced by notebooks 01–03, rendered by a separate
> figure script). Prose states the **established direction** (F-findings already produced from real
> DB6 in notebooks 01–02); the numeric backbone lands here when the CSVs do.

**3.1 Signal quality (notebook 01).** `TABLE PENDING` — QC rejection rate per session.
Established (F2/F5): rejection is low-single-digit median with one anomalous session; the advisory
`noise_burst` mode is **under-covered** by amplitude features and needs band-power or must fall to
the IMU cross-check (F5).

**3.2 Baseline across protocols (notebook 02).** `TABLE PENDING` — balanced accuracy, four
protocols × {binary, multi-class}. Established:
- **F1 — the thesis holds:** cross-session **ECE roughly doubles-to-triples while balanced accuracy
  falls only a few points.** Accuracy-stable, calibration-degraded = the gate-opening failure.
- **F2 — drift is episodic, not gradual:** degradation is flat across elapsed sessions except one
  anomalous session; two independent routes (QC + accuracy) reach the same shape. The problem is
  *event detection*, not slow drift.
- **F3 — Reborn's own task barely drifts:** binary loses little cross-session, multi-class loses
  much more. The threat *to Reborn specifically* is milder than the gesture-recognition literature
  implies, and the paper says so.
- **F4 — cross-subject is not the worst case for binary** (matches/beats cross-session) → less
  few-shot headroom on the binary task than assumed; headroom is **tested, not presupposed**.
- **F6 — two channels cap multi-class, not binary:** the low multi-class ceiling is a montage limit
  and must never be compared to 14-channel literature.

**3.3 Calibration under drift + few-shot (notebook 03 — the core figure).** `FIGURES PENDING —
notebook 03 not yet run.` Planned: ECE-vs-accuracy divergence across protocols; gate-threshold sweep
(unsafe-assist vs availability); direct investigation of the one anomalous session; few-shot
**repetition** sweep (n ∈ {1,2,4,8}) posed as "how many repetitions restore *safe* behaviour",
gated on first confirming headroom exists (F4).

## 4. Discussion

The central result reframes drift for a safety-first system: the danger is **calibration decay under
preserved accuracy** (F1), and it arrives as **events, not a trend** (F2) — so the right response is
anomaly/event detection feeding the confidence gate, not scheduled recalibration. Because Reborn's
binary energy decision is comparatively drift-robust (F3), the ML layer's honest role is *advisory
and bounded*: it can lower assist on low confidence, never raise it. This is the empirical hand-off
to phase D (`papers/architecture_position`).

## 5. Conclusion

`TBD — after §3 is complete.`

## 6. Limitations

- **Domain gap** — forearm datasets, elbow target; claim is about method, not physiology (§2).
- **Two-channel montage** caps multi-class (F6); binary conclusions unaffected.
- **DB6 subset so far** (s01–s02) — full DB6, putEMG replication, and EPN-612 few-shot are the
  external-validity arms, still pending (`phase-b-plan.md` §9 steps 6–7).
- **`noise_burst` coverage gap** (F5) until a band-power feature is added.
- Single dataset family for the main claim; single montage; offline replay, not live hardware.

## 7. Reproducibility

Manuscript cites the git tag of the code and the cache `manifest.json` its figures came from.
Committed aggregated tables → `results/`; bulky per-window output stays in git-ignored
`experiments/results/`. Figures rendered by a standalone script from the committed CSVs, never from a
live kernel.

## References

`TBD — Zotero export; seeded by phase A (papers/review_adherence/references).`
