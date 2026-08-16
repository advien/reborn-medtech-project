# Adherence in rehabilitation robotics: how it is defined, measured, and influenced — a scoping review

**Draft manuscript — Phase A.** Reported per **PRISMA-ScR** (Tricco et al. 2018). Companion to
[`protocol.md`](protocol.md) (the reproducibility contract), [`README.md`](README.md), and
[`prisma-flow.md`](prisma-flow.md). Target venue: open-access journal / arXiv preprint
(`docs/roadmap.md`).

> **Status: PRISMA-ScR skeleton.** Background, review questions, and methods are real (drawn from
> the frozen protocol). **No search has been run**, so every results / synthesis section is a `TBD`
> marker naming the process artifact that will fill it (search-log → screening → extraction → PRISMA
> flow). Per the integrity note in `protocol.md`, nothing about *what the literature says* is written
> until the logged search-and-screen process produces it. Per `research-context.md` §6–7, no novelty
> is assumed.

---

## Abstract (structured, PRISMA-ScR)

`TBD — written last.` **Objective:** map how adherence is defined, measured, and influenced in
rehabilitation robotics, and locate gaps — especially whether adherence is ever linked to the
*appropriateness* of assistance (the Reborn axis). **Methods:** scoping review, N sources, search
dates `TBD`. **Results:** `N` records screened, `k` included (`TBD` from PRISMA flow). **Conclusion:**
`TBD`.

## 1. Introduction / rationale

Reborn studies the decision-making of an assistive robotic system under uncertainty — *appropriate*
rather than *maximal* assistance (`research-context.md`). Adherence is the behavioural hinge: an
assistance policy users abandon delivers no rehabilitation regardless of its control-theoretic
merits, and assist-as-needed strategies are motivated partly by their presumed effect on engagement
and active participation. This review maps what is already known so later phases (B: intent/ML;
C: control & fail-safe; D: architecture) target real, unsolved problems. It is the solo-feasible
reformulation of roadmap topic 1 (an original behavioural study, infeasible solo) into a literature
review.

**Objective and review questions** (PCC framing in `protocol.md` §2):

- **RQ1 — Definition.** How is adherence (and near-synonyms: compliance, engagement, usage,
  persistence) defined in rehabilitation-robotics research?
- **RQ2 — Measurement.** What metrics/instruments quantify it (session counts, dose, active time,
  self-report scales, sensor-derived usage, dropout/attrition)?
- **RQ3 — Influencing factors.** What motivational / clinical / technological factors (including the
  assistance strategy itself) are reported to raise or lower it?
- **RQ4 — Gaps.** Where are the gaps — in particular, is adherence ever linked to the
  *appropriateness* of assistance or to system trust/safety? *This is the bridge to phases B–D.*

## 2. Methods

Full protocol in [`protocol.md`](protocol.md); this section is its reporting-stage summary.

- **Review type & reporting.** Scoping review per PRISMA-ScR; not an effectiveness synthesis.
  Escalation to a systematic review reconsidered and logged only if the evidence base proves narrow
  and homogeneous.
- **Eligibility** (`protocol.md` §3). Rehabilitation-robotics / powered-orthosis context; reports
  adherence as definition, measurement, influencing factor, or outcome (not a passing mention);
  human users; English; retrievable full text. Exclusion reason codes in
  [`screening/inclusion-exclusion.md`](screening/inclusion-exclusion.md).
- **Information sources** (`protocol.md` §4). PubMed/MEDLINE, Scopus (or WoS), IEEE Xplore,
  Semantic Scholar, arXiv, Google Scholar; backward + forward snowballing via Semantic Scholar.
  Zotero as reference manager.
- **Search strategy.** Concept blocks and per-database strings in
  [`search/search-strategy.md`](search/search-strategy.md); every executed query logged in
  [`search/search-log.csv`](search/search-log.csv). `Search dates: TBD.`
- **Selection.** Dedup in Zotero → title/abstract → full text. Solo-reviewer consistency via a
  **10% re-screen after ≥1 week (Cohen's κ)** — the honest substitute for dual screening.
- **Data charting.** Fields mapped to RQ1–RQ4 in
  [`extraction/extraction-fields.md`](extraction/extraction-fields.md).
- **Synthesis.** Descriptive/narrative: a taxonomy of adherence metrics (RQ1–RQ2), clustered
  influencing factors (RQ3), a gap map (RQ4). No meta-analysis.

## 3. Results

> All of §3 is `TBD` — produced only by the executed search-and-screen process. Placeholders name
> their source artifact.

**3.1 Search and selection.** `PRISMA FLOW PENDING` — records identified per source, after dedup,
title/abstract-screened, full-text-assessed, excluded (with reason-code breakdown), included. Live
counts tracked in [`prisma-flow.md`](prisma-flow.md); intra-rater κ reported here. `Figure 1: PRISMA
flow diagram — TBD.`

**3.2 Characteristics of included studies.** `TABLE PENDING` (`extraction-template.csv`) —
population/condition, device type, assistance strategy, study design, year.

**3.3 RQ1 — how adherence is defined.** `TBD` — narrative + definition table.

**3.4 RQ2 — how it is measured.** `TBD` — **taxonomy of adherence metrics/instruments** (the
review's main descriptive product).

**3.5 RQ3 — influencing factors.** `TBD` — clustered motivational / clinical / technological.

**3.6 RQ4 — gaps.** `TBD` — coverage map; explicitly whether *appropriateness of assistance* and
trust/safety appear at all.

## 4. Discussion

`TBD — after §3.` Will foreground RQ4: whether the field links adherence to appropriateness of
assistance, and what that gap (or its absence) implies as the explicit input to phases B–D. Must not
assert novelty until the map itself supports or refutes it.

## 5. Limitations

Declared up front (`protocol.md` §10): **single reviewer** (mitigated by 10% re-screen + κ);
**English-only** at this stage; **no effect-size synthesis** (by design — this maps the field).

## 6. Conclusion

`TBD.`

## Reporting & reproducibility

PRISMA-ScR checklist completed at write-up (`prisma-scr-checklist.md`, added at reporting stage).
The chain protocol → search-log → screening → extraction → references is versioned together; the
manuscript cites the git tag it was executed from.

## References

`TBD — Zotero export under references/ (RIS/BibTeX committed, PDFs git-ignored).`
