# Review: adherence in rehabilitation robotics

**Phase A** ([`docs/roadmap.md`](../../docs/roadmap.md)). A **scoping review**, reported per
PRISMA-ScR, of how adherence is *defined*, *measured*, and *influenced* in rehabilitation robotics —
the reformulation of roadmap topic 1 ("behavioural study", infeasible solo) into a literature review
(fully feasible solo). It is the first publishable output and the literature map every later phase
draws on (`docs/research/research-context.md` §10).

> **Not yet executed.** This folder is the *executable scaffold* — protocol, search strings,
> templates, and trackers. No search has been run and no findings exist yet. Nothing is filled in
> until the logged process below produces it (integrity note in [`protocol.md`](protocol.md)).

## What's here

| File | Purpose |
|---|---|
| [`protocol.md`](protocol.md) | The review protocol (PRISMA-ScR): questions, eligibility, sources, methods. The reproducibility contract. |
| [`search/search-strategy.md`](search/search-strategy.md) | Concept blocks + draft per-database search strings + calibration procedure. |
| [`search/search-log.csv`](search/search-log.csv) | Every executed query, date, and hit count. |
| [`search/seed-set.md`](search/seed-set.md) | Known-relevant papers for testing search recall. |
| [`screening/inclusion-exclusion.md`](screening/inclusion-exclusion.md) | Operational criteria + exclusion reason codes. |
| [`screening/screening-template.csv`](screening/screening-template.csv) | T/A + full-text screening decisions. |
| [`extraction/extraction-fields.md`](extraction/extraction-fields.md) | Data-charting field definitions (mapped to RQ1–RQ4). |
| [`extraction/extraction-template.csv`](extraction/extraction-template.csv) | The charting form. |
| [`prisma-flow.md`](prisma-flow.md) | Live record counts for the PRISMA flow diagram. |
| [`references/`](references/) | Zotero export (bibliography) — PDFs git-ignored. |

## Workflow (how to execute Phase A)

1. **Freeze the protocol.** Review [`protocol.md`](protocol.md); when happy, this becomes the
   git-tagged version the eventual paper cites.
2. **Calibrate the search.** Pilot the draft strings, test against the seed set, adjust, then
   freeze to `v1.0` (procedure in `search/search-strategy.md`). Log every run.
3. **Run + dedup.** Execute final searches, import to Zotero, deduplicate, record counts in
   `prisma-flow.md`.
4. **Screen.** Title/abstract → full text, using the reason codes. Do the 10% re-screen for κ.
5. **Chart.** Extract included studies into the charting form.
6. **Synthesise.** Build the adherence-metric taxonomy, cluster influencing factors, map gaps —
   foregrounding whether *appropriateness of assistance* (the Reborn axis, RQ4) appears at all.
7. **Write up + tag.** Draft the paper, complete the PRISMA-ScR checklist, tag code+protocol+refs.

## Reproducibility

The chain protocol → search-log → screening → extraction → references is versioned together, so any
number in the paper traces back to the query and decision that produced it. The manuscript cites the
specific git tag it was generated from.
