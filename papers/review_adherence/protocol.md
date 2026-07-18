# Phase A — Scoping review protocol

**Working title:** *Adherence in rehabilitation robotics: how it is defined, measured, and
influenced — a scoping review.*

**Status:** protocol draft `v0.1`. This document is written *before* the search is run. It is
the reproducibility contract: the paper that comes out of Phase A must cite the git tag of the
protocol version it was executed from (see `docs/roadmap.md`).

**Review type:** scoping review, reported per **PRISMA-ScR** (PRISMA Extension for Scoping
Reviews, Tricco et al. 2018). A scoping review — not a systematic review of effectiveness — is
the right instrument here: the goal is to *map* how adherence is conceptualised and measured in
this field and to locate gaps, not to pool effect sizes. If, during title/abstract screening, the
evidence base turns out to be narrow and homogeneous enough to support a focused effectiveness
question, escalation to a systematic review is reconsidered and recorded in the changelog.

> **Integrity note.** No result, count, included study, or finding is written into this repository
> until it has actually been produced by the logged search-and-screen process below. Placeholders
> are marked `TBD`. This protocol is scaffolding; it does not pre-suppose what the literature says.
> Per `docs/research/research-context.md` §6–7, no novelty is assumed.

---

## 1. Background & rationale

Reborn studies the decision-making of an assistive robotic system under uncertainty — the question
of *appropriate* assistance rather than *maximal* assistance
(`docs/research/research-context.md`). Adherence is the behavioural hinge of that question: an
assistance policy that users abandon delivers no rehabilitation regardless of its control-theoretic
merits, and "assist-as-needed" strategies are motivated in part by their presumed effect on
engagement and active participation.

Phase A maps what is already known about adherence in rehabilitation robotics so that later phases
(B: intent/ML; C: control & fail-safe; D: architecture) target real, unsolved problems rather than
re-deriving established results. This review is the reformulation of roadmap topic 1 ("original
behavioural study", infeasible solo) into a literature review (fully feasible solo).

## 2. Objectives & review questions

**Overall objective.** Map the concepts, measurement instruments, influencing factors, and
evidence gaps for *adherence* to robot-assisted / robotic rehabilitation and assistive orthotic
regimens.

Framed with the **PCC** mnemonic recommended for scoping reviews:

| Element | Scope |
|---|---|
| **P**opulation | People undergoing motor rehabilitation or using an assistive orthosis/exoskeleton (any age, any condition — stroke, SCI, MS, orthopaedic, etc.). |
| **C**oncept | Adherence / compliance / engagement / usage / dropout — how it is **defined**, **measured**, and what **influences** it. |
| **C**ontext | Rehabilitation robotics: robot-assisted therapy, wearable/assistive robots, powered orthoses and exoskeletons. Clinic, lab, or home. |

**Review questions.**

- **RQ1 — Definition.** How is adherence (and its near-synonyms: compliance, engagement, usage,
  persistence) defined in rehabilitation-robotics research?
- **RQ2 — Measurement.** What metrics and instruments are used to quantify it (e.g. session
  counts, dose, active time, self-report scales, sensor-derived usage, dropout/attrition)?
- **RQ3 — Influencing factors.** What factors — motivational, clinical, technological (including
  the assistance strategy itself, e.g. assist-as-needed vs. fixed) — are reported to increase or
  decrease adherence?
- **RQ4 — Gaps.** Where are the gaps? In particular: is adherence ever linked to the
  *appropriateness* of assistance or to system trust/safety, the axis Reborn cares about?

RQ4 is the bridge to the rest of the programme; RQ1–RQ3 are the descriptive map.

## 3. Eligibility criteria

Criteria are applied in two stages (title/abstract, then full text). Every exclusion at full-text
stage is recorded with a single primary reason code (see `screening/inclusion-exclusion.md`).

**Include if all of:**
- Concerns a rehabilitation-robotics or powered/assistive-orthosis/exoskeleton context.
- Reports on adherence/compliance/engagement/usage/dropout as a **definition, a measurement, an
  influencing factor, or an outcome** — not merely mentioning the word in passing.
- Primary study, review, or methods/position paper.
- Human users (patients or healthy participants standing in for them).

**Exclude if any of:**
- Purely mechanical/control paper with no adherence, usage, engagement, or dropout dimension.
- Robotics absent (e.g. conventional physiotherapy adherence with no robotic/orthotic device) —
  *unless* used explicitly as a comparator for a robotic arm.
- Not retrievable in full text.
- Not in English (recorded but excluded at this stage; language is a known scoping limitation).
- Non-research item (editorial, abstract-only conference item with no extractable data, patent).

**Date range.** No lower bound at protocol time (rehabilitation robotics is a young field); the
actual earliest hit is reported in the PRISMA flow. Search re-run date is logged.

## 4. Information sources

| Source | Role | Notes |
|---|---|---|
| **PubMed / MEDLINE** | Primary (clinical) | MeSH + free-text. Authoritative for rehabilitation. |
| **Scopus** *(or Web of Science if no access)* | Primary (multidisciplinary) | Engineering + clinical overlap; good citation tooling. |
| **IEEE Xplore** | Primary (engineering) | Where the robotics/control literature actually lives. |
| **Semantic Scholar** | Supplementary + API | Programmatic search, citation graph, snowballing. |
| **arXiv** | Supplementary | Preprints (ML/control) not yet indexed elsewhere. |
| **Google Scholar** | Supplementary | Grey literature + forward citation checking; first N results only, logged. |

**Snowballing.** Backward (reference lists) and forward (citing articles) chasing on included
studies, via Semantic Scholar's citation graph. Logged as a separate source in the PRISMA flow.

**Reference manager.** Zotero. The exported library (RIS/BibTeX) lives under `references/`;
raw data files are git-ignored, only the export and notes are committed.

## 5. Search strategy

Concept blocks, database-specific strings (draft `v0.1`), and the calibration procedure are in
[`search/search-strategy.md`](search/search-strategy.md). Every executed query is recorded in
[`search/search-log.csv`](search/search-log.csv) with database, date, exact query string, and hit
count, so the search is reproducible and the PRISMA flow numbers are traceable.

## 6. Selection process

1. Export all hits from all sources into Zotero; deduplicate (Zotero duplicate detection, then
   manual check). Record counts before/after dedup.
2. **Title/abstract screening** against §3 criteria, logged in
   [`screening/screening-template.csv`](screening/screening-template.csv).
3. **Full-text screening** of everything that passed, with one primary exclusion reason code each.
4. As a solo reviewer, calibrate consistency by re-screening a **random 10% sample** after a
   ≥1-week gap and reporting intra-rater agreement (Cohen's κ). This is the honest solo substitute
   for dual independent screening; the single-reviewer limitation is stated explicitly in the
   paper.

## 7. Data charting (extraction)

Charted fields and their definitions are in
[`extraction/extraction-fields.md`](extraction/extraction-fields.md); the form itself is
[`extraction/extraction-template.csv`](extraction/extraction-template.csv). Fields map directly to
RQ1–RQ4 (definition used, metric/instrument, influencing factors, population/condition, device
type, assistance strategy, whether appropriateness/trust/safety is linked to adherence).

## 8. Synthesis

Descriptive / narrative synthesis appropriate to a scoping review:
- Tabulate definitions and measurement instruments (RQ1–RQ2) → a **taxonomy of adherence metrics**.
- Cluster influencing factors (RQ3) → motivational / clinical / technological.
- Map coverage and gaps (RQ4), foregrounding whether the "appropriate assistance" axis appears at
  all. Gaps become the explicit input to phases B–D.

No meta-analysis; heterogeneity of designs and outcomes is expected and is itself a finding.

## 9. Reporting

PRISMA-ScR checklist completed at write-up (`prisma-scr-checklist.md`, added at the reporting
stage). PRISMA flow diagram counts tracked live in
[`prisma-flow.md`](prisma-flow.md).

## 10. Limitations (declared up front)

- **Single reviewer** — mitigated by the 10% re-screen + κ (§6), stated as a limitation.
- **English-only** at this stage — a known scoping constraint.
- **No effect-size synthesis** — by design; this maps the field, it does not adjudicate efficacy.

## 11. Changelog

| Version | Date | Change |
|---|---|---|
| v0.1 | TBD (this commit) | Initial protocol scaffold. No search executed yet. |
