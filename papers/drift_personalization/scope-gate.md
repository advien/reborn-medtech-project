# Paper A — Contribution & Novelty Positioning Gate

*Decision artifact. Freezes scientific scope before final experiments/writing. Uses
only evidence already in hand: full-DB6 results (`results/fulldb6_*.csv`,
`research-ledger.md`) and the related-work probe (`related-work-calibration.md`).
No new experiments run here.*

Legend: ESTABLISHED / PARTIALLY ESTABLISHED / UNCLEAR / POTENTIALLY NOVEL.

---

## TASK 1 — Claim-by-claim novelty audit

| # | Candidate claim | Already established? | Strongest relevant prior work | What our DB6 study adds | Evidence we have | Novelty | Keep/Drop |
|---|---|---|---|---|---|---|---|
| 1 | Cross-session sEMG drift reduces classification performance | ESTABLISHED | Whole cross-day EMG field (ViT-MDHGR 2309.12602; Fratti 2024; Trifena 2025) | Nothing | Δacc binary 0.072 | none | Drop→background |
| 2 | Probability calibration degrades under distribution shift | ESTABLISHED | Ovadia 2019; Guo 2017 | Nothing (general ML) | our ECE ratios | none | Drop→background |
| 3 | Probability calibration degrades across sEMG sessions | PARTIALLY ESTABLISHED | Trifena 2025 (ECE 1.8→3.6, weak venue) | Public benchmark, n=10, reproducible | ECE 0.028→0.051/0.060 | weak–moderate | Keep (support) |
| 4 | Calibration deteriorates **disproportionately** vs accuracy | PARTIALLY ESTABLISHED / UNCLEAR | Trifena's own table contains it but **unremarked**; Ovadia (general) | Explicit quantification + **naming** it; n=10, both tasks | ECE ×2.0 vs acc −8% rel | **moderate** | **Keep (core)** |
| 5 | Confidence-gated myoelectric control becomes less reliable under session drift | PARTIALLY ESTABLISHED / UNCLEAR | Rejection line (Scheme & Hudgins); Trifena uses gating in-session | Show the gate **operating point shifts** across sessions | unsafe-act 0.059→0.095 (default gate); B6 pilot | moderate | Keep (consequence) |
| 6 | Low within-session ECE ≠ trustworthy confidence cross-session | UNCLEAR / POTENTIALLY NOVEL (as stated warning) | Implied by Ovadia; Trifena concludes "well-calibrated" (i.e. misses it) | Explicit warning for myoelectric gating | within 0.028 → cross 0.051 | moderate | **Keep (framing)** |
| 7 | Calibration degradation differs substantially between subjects | UNCLEAR / POTENTIALLY NOVEL | EMG accuracy heterogeneity known; calibration heterogeneity not found | Per-subject ECE ratio 0.89–3.65; worse in 8/10 (LDA) | per-subject CSV | moderate | Keep (secondary) |
| 8 | Binary vs multi-class respond differently to drift | PARTIALLY ESTABLISHED | Intuitive; Trifena (multi worse cross-subject) | Quantified: Δ0.072 vs 0.164; ECE ×2 vs ×3.4–5.2 | aggregate CSV | weak | Keep (support) |
| 9 | Per-subject calibration/performance dissociation | UNCLEAR / POTENTIALLY NOVEL | = #4 ∧ #7; not found reported in sEMG | Subject-level dissociation with spread | per-subject CSV | moderate | Keep (=core+sec) |
| 10 | QC abnormalities ↔ calibration/performance degradation | POTENTIALLY NOVEL but unevidenced | Not found | Would be new IF shown | descriptive only (QC 0.10–6.55%); **not tested** | unknown | Drop→optional |
| 11 | Unsafe-assist vs availability trade-off shifts under drift | UNCLEAR | Rejection ROC exists; session-shift of operating point not found | Trade-off curve within vs cross, n=10 | B6 pilot (n=2) + default-gate point | moderate | Keep (needs sweep) |
| 12 | Few-shot recovers calibration vs accuracy differently | POTENTIALLY NOVEL | Few-shot recalibration exists (accuracy); cal-vs-acc recovery not found | Would be new | **none (not run)** | unknown | **Drop (this paper)** |

**Reading:** claims 1–2 are pure background. The live nucleus is **#4/#6/#9** (the
dissociation, its non-transfer as a warning, its per-subject spread), with **#5/#11**
as the engineering consequence and **#3/#7/#8** as support. #10/#12 are out.

---

## TASK 2 — Strongest defensible contribution (top 3)

**C1 — Systematic, reproducible, per-subject characterization of the
calibration-vs-performance dissociation on public DB6.**
- *Why scientific:* turns a scattered/uninterpreted observation into a controlled,
  reproducible benchmark result with subject-level uncertainty.
- *Why myoelectric:* confidence is the signal a gate consumes; if it decays faster
  than accuracy, gating logic tuned in-session is on sand.
- *Evidence now:* full DB6 n=10 (ECE ×2.0 vs acc −8% rel; worse 8–10/10). Strong.
- *Additional needed:* subject-level stats/CIs; a proper scoring rule (NLL/Brier).
- *Novelty risk:* MEDIUM (Trifena has the raw pattern; general ML has the effect).
- *Overclaim risk:* MEDIUM (must not say "first").

**C2 — Trustworthiness warning: in-session calibration does not transfer.**
- *Why:* a directly actionable caution — low in-session ECE licenses nothing after a
  day. Hard to overclaim (it is a limitation result).
- *Why myoelectric:* speaks to deployment/validation practice for gated decoders.
- *Evidence now:* within 0.028 → cross 0.051; heterogeneous. Good.
- *Additional needed:* same stats as C1; frame explicitly.
- *Novelty risk:* MEDIUM. *Overclaim risk:* LOW.

**C3 — Confidence-gate operating-point non-transfer.**
- *Why:* an in-session-tuned threshold changes its false-activation/availability
  balance across sessions.
- *Why myoelectric:* concrete engineering consequence for gate design.
- *Evidence now:* B6 pilot (n=2) + default-gate point (n=10); **needs the full sweep
  on n=10.** *Novelty risk:* MEDIUM. *Overclaim risk:* HIGH (terminology/safety).

**Recommended PRIMARY:** **C1**, stated through the **C2 lens** (the warning), with
**C3 as a bounded consequence** and per-subject heterogeneity as the reason
aggregates mislead. This is the narrowest defensible nucleus: *measure the
dissociation rigorously; conclude that in-session calibration does not transfer.*

---

## TASK 3 — Four framings scored (1–5; higher = better/safer)

| Framing | Novelty | Evidence | Low burden | Clinical relevance | Low overclaim risk | Feasible in scope | Total |
|---|--:|--:|--:|--:|--:|--:|--:|
| **A** Calibration dissociation | 3 | 5 | 5 | 4 | 3 | 5 | **25** |
| **B** Trustworthiness warning | 3 | 4 | 4 | 5 | 5 | 5 | **26** |
| **C** Inter-individual heterogeneity | 4 | 3 | 4 | 4 | 3 | 4 | **22** |
| **D** Confidence-gate safety | 3 | 3 | 3 | 4 | 2 | 4 | **19** |

- **A**: backbone; strongest evidence; novelty capped by Trifena/Ovadia.
- **B**: most *defensible* — safety-relevant, honest, near-impossible to overclaim,
  fully evidenced. Highest total.
- **C**: least-covered (best novelty) but n=10 is thin to carry a "user-dependent"
  claim alone.
- **D**: weakest — evidence incomplete and "unsafe/safety" terminology is a reviewer
  magnet on intact-subject offline data.

**Most defensible single framing = B**, resting on A as the mechanism, using C to
explain why aggregates hide it. **Not** D as the headline.

---

## TASK 4 — Can framing A be strengthened (not replaced)?

**PRIMARY** (characterize dissociation on DB6) + **SECONDARY** (per-subject
heterogeneity ⇒ aggregates hide it) + **CONSEQUENCE** (in-session gate thresholds
don't preserve the trade-off) — **is ONE coherent paper.** It is a single causal
chain at three resolutions:

> drift → (accuracy holds, calibration decays: **A**) → (unevenly across users, so
> the mean lies: **C**) → (therefore a gate validated in-session mis-operates later:
> **D-bounded**).

It is **not** too many contributions: they are one claim (A) plus its *variance* (C)
and its *consequence* (D), not three independent findings. **Condition:** D must be
an *illustration with operational terminology*, not a safety claim, or it re-inflates
overclaim risk. Verdict: **coherent — build this.**

---

## TASK 5 — Literature questions that MUST be resolved (≤5)

Prioritised by pre-emption risk. Run once on IEEE Xplore / Scopus / Semantic Scholar.

1. **[Direct pre-emption]** Does any *credible* peer-reviewed sEMG paper explicitly
   state that calibration/ECE degrades **more than** accuracy across sessions?
   `TITLE-ABS-KEY((EMG OR electromyograph*) AND ("calibration error" OR ECE OR "reliability diagram") AND (session OR cross-day OR inter-day OR cross-session))`
2. **[Gate transfer]** Has session-dependence of a confidence-based rejection/gating
   *operating point* been reported in myoelectric control?
   `("myoelectric" OR EMG) AND (rejection OR "confidence-based" OR "reject option") AND (session OR day OR non-stationar*)`
3. **[Benchmark dup]** Has ECE / a reliability diagram been reported on **NinaPro**
   specifically (any DB)?
   `"Ninapro" AND (calibration OR ECE OR "reliability diagram" OR "temperature scaling")`
4. **[Warning stated]** Is "in-distribution calibration does not transfer under shift"
   already stated for biosignals/EMG/BCI (beyond general-ML Ovadia)?
   `(EMG OR biosignal OR "brain-computer") AND ("temperature scaling" OR calibration) AND (shift OR generaliz* OR out-of-distribution)`
5. **[Heterogeneity]** Any prior on subject-level heterogeneity of *calibration* under
   shift (to protect the secondary)?
   `(EMG OR electromyograph*) AND calibration AND (subject-specific OR inter-subject OR heterogen*)`

If Q1 or Q2 returns a credible direct hit for the full A+D chain → pivot headline to
**B/C** (still defensible) and cite the hit.

---

## TASK 6 — Experiment triage

**MUST COMPLETE (support the primary claim):**
- **Subject-level statistics + uncertainty** (per-subject as the unit; CIs /
  Wilcoxon on within→cross ΔECE, Δacc) — without this, n=10 pooled is pseudoreplicated.
- **Proper scoring rule alongside ECE** (NLL and/or Brier) + binning-robust/adaptive
  ECE — ECE alone is a known-fragile metric; reviewers will demand this.
- **Gate operating-point transfer (minimal):** apply an in-session-tuned threshold
  cross-session and report the false-activation/availability shift, n=10 — needed for
  the consequence; keep terminology operational.

**SHOULD COMPLETE IF TIME (materially strengthens, not required):**
- Per-subject **episodic vs gradual** characterization — deepens C.
- **One alternative montage** (e.g. more channels) — pre-empts "montage-specific".

**DROP FROM THIS PAPER (scope creep):**
- **Full elaborate unsafe-assist/availability sweep** as a headline — keep only the
  minimal transfer check above; the full sweep is a second paper.
- **QC ↔ calibration association** — tangential, unevidenced; descriptive mention only.
- **Few-shot personalization** — no evidence yet; own paper.
- **Band-power / noise-burst (anomaly detector) work** — different (input-monitor)
  line, not calibration.
- **putEMG replication** — great external validity but not feasible in the current scope.
- **EMG-EPN-612** — different hardware (Myo, 8-ch); future.
- **Additional ML models (CNN, etc.)** — a bigger model adds accuracy, not the
  calibration insight; a simple model making the point is the point.
- **IMU fusion** — explicitly out of scope.

---

## TASK 7 — Skeptical reviewer: 7 strongest rejection risks

| # | Rejection risk | Severity | Fixable in scope? | Minimum action |
|---|---|---|---|---|
| 1 | **Novelty** — "calibration-under-shift is known (Ovadia/Guo); ECE-in-EMG exists (Trifena)" | HIGH | Yes | Tight related-work; claim only the increment (systematic public-benchmark + naming + non-transfer); credit priors explicitly |
| 2 | **External validity** — n=10, intact subjects, offline, DB6 only | HIGH | Yes (scope) | State method-level scope; no clinical/amputee/real-world extrapolation |
| 3 | **Pseudoreplication/independence** — overlapping windows + pooled splits treated as independent | HIGH | Yes | Subject as unit of analysis; per-subject stats + CIs; no pooled-window significance |
| 4 | **"Unsafe-assist" overclaims safety** on intact offline data | MED–HIGH | Yes | Rename to operational term (e.g. "rest-phase false-activation rate under gate G"); explicit disclaimer |
| 5 | **ECE limitations** — binning-sensitive, improper; ratio unstable at small ECE | MED | Yes | Add NLL/Brier; adaptive-bin ECE; report absolute values + CIs, not only ratios |
| 6 | **Montage** — 2 of 14 channels, arguably unrepresentative | MED | Partly | Justify (mirrors low-channel systems) + limitation; optionally 1 alt montage |
| 7 | **So-what / effect size** — Δacc 0.07, ECE 0.028→0.051 look small | MED | Yes | Frame relative (ECE ~doubles) + the per-subject tail (×3.6) + the gate consequence |
| + | **elimensi pre-emption** — a paper already has the table | MED | Yes | Cite + differentiate (they report-but-don't-interpret; we characterise + name + stats) |

None are fatal *if* addressed. #1–#4 are the make-or-break and are all fixable by
scoping and statistics rather than new data.

---

## TASK 8 — Frozen scientific scope

### RECOMMENDED PRIMARY RESEARCH QUESTION
Under cross-session drift on public NinaPro DB6, does the probability calibration of a
surface-EMG intent decoder degrade disproportionately relative to its classification
accuracy — such that confidence validated within-session does not remain trustworthy
across sessions?

### PRIMARY CONTRIBUTION
A systematic, reproducible, per-subject characterization on public DB6 (n=10) showing
that cross-session drift degrades confidence calibration substantially more (in
relative terms) than it degrades balanced accuracy in binary myoelectric intent
decoding — so in-session calibration/gate settings do not transfer across sessions.

### SECONDARY CONTRIBUTIONS (≤2)
1. The dissociation is strongly **subject-heterogeneous**, so aggregate accuracy/ECE
   hides materially different confidence-reliability behaviour.
2. **Binary** rest-vs-movement is more accuracy-robust to drift than **multi-class**,
   yet both exhibit the calibration≫performance dissociation.

### CLAIMS WE MUST NOT MAKE (≤6)
1. That we discovered calibration-under-drift, or first used ECE / confidence-gating /
   observed cross-session calibration change.
2. Any clinical, amputee/prosthesis-user, or real-world safety/harm claim.
3. That "false-activation/unsafe" numbers reflect real device or patient risk.
4. Generalization beyond DB6 / intact subjects / this 2-channel montage / these models.
5. That the effect is universal across subjects (it is heterogeneous, 8–10/10).
6. Any causal claim linking QC abnormalities to calibration loss.

### REQUIRED REMAINING EXPERIMENTS
- Subject-level statistics + uncertainty (CIs / Wilcoxon) for within→cross ΔECE and Δacc.
- Proper scoring metric (NLL and/or Brier) + binning-robust ECE.
- Minimal gate operating-point transfer check on n=10 (operational terminology).

### OPTIONAL EXPERIMENTS (≤3)
- Episodic-vs-gradual per-subject characterization.
- One alternative montage (robustness).
- Descriptive QC-vs-degradation look (no causal claim).

### WORKING TITLES (conservative)
1. *Confidence Calibration Degrades More Than Accuracy Under Cross-Session Drift in
   Surface-EMG Intent Decoding: A NinaPro DB6 Study.*
2. *In-Session Calibration Does Not Transfer: Cross-Session Confidence Reliability of
   Myoelectric Intent Decoding on NinaPro DB6.*
3. *Accuracy Holds, Confidence Does Not: A Reproducible Characterization of Calibration
   Drift Across Surface-EMG Sessions.*

### GO / NO-GO
**CONDITIONAL GO.** Proceed toward the paper **iff**:
1. Task-5 Q1–Q3 find **no credible peer-reviewed paper** that already names the
   dissociation *and* the gate-transfer consequence (weak-venue Trifena does not
   pre-empt; a credible one would force a pivot to B/C);
2. subject-level statistics preserve the dissociation with uncertainty (not carried by
   1–2 subjects);
3. terminology is rescoped (drop "unsafe-assist" as a safety term; drop clinical
   framing).
If (1) fails for the full chain → **pivot headline to B (warning) + C (heterogeneity)**,
which remain defensible. If (2) fails → **NO-GO** as a positive-finding paper (report
as a null/heterogeneity note instead).
