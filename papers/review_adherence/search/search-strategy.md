# Search strategy — `v1.0` (frozen 2026-08-13)

Concept blocks and database-specific query strings for the Phase A scoping review
([`../protocol.md`](../protocol.md)). These are a **draft to be calibrated**, not final. The
procedure below (pilot search → adjust → freeze → run) is standard for a reproducible review.

> Every run — pilot or final — is logged in [`search-log.csv`](search-log.csv) with the exact
> string and hit count. The PRISMA flow numbers must be traceable back to those rows.

---

## Concept blocks

The query is the AND of two mandatory blocks. Block C is an optional refinement used only if
Block A AND B returns an unmanageable volume.

**Block A — rehabilitation robotics / assistive device** (context)
> rehabilitation robot*, robot-assisted, robotic therapy, exoskeleton, powered orthosis,
> orthotic, wearable robot, assistive device, end-effector robot, exosuit

**Block B — adherence** (concept)
> adherence, compliance, engagement, usage, use pattern, dropout, drop-out, attrition, retention,
> persistence, abandonment

**Block C — measurement / motivation** (optional refinement)
> measure*, metric, assessment, self-report, questionnaire, motivation, self-efficacy, dose,
> session*

---

## Database-specific strings

### PubMed / MEDLINE (draft)

```
(
  "rehabilitation robotics"[tiab] OR "rehabilitation robot*"[tiab] OR "robot-assisted"[tiab]
  OR "robotic therapy"[tiab] OR exoskeleton*[tiab] OR "powered orthos*"[tiab]
  OR orthotic*[tiab] OR "wearable robot*"[tiab] OR exosuit*[tiab]
  OR "Robotics"[Mesh] OR "Exoskeleton Device"[Mesh]
)
AND
(
  adherence[tiab] OR compliance[tiab] OR engagement[tiab] OR usage[tiab]
  OR dropout[tiab] OR "drop-out"[tiab] OR attrition[tiab] OR retention[tiab]
  OR persistence[tiab] OR abandonment[tiab]
  OR "Patient Compliance"[Mesh] OR "Treatment Adherence and Compliance"[Mesh]
)
AND
(
  "Rehabilitation"[Mesh] OR rehabilitation[tiab] OR therapy[tiab]
)
```
*Calibration note:* the third (rehabilitation) clause guards against exoskeleton hits from
industrial/military contexts. Drop it if recall suffers.

### Scopus / Web of Science (draft)

```
TITLE-ABS-KEY(
  ( "rehabilitation robot*" OR "robot-assisted" OR "robotic therapy" OR exoskeleton*
    OR "powered orthos*" OR orthotic* OR "wearable robot*" OR exosuit* )
  AND
  ( adherence OR compliance OR engagement OR usage OR dropout OR "drop-out"
    OR attrition OR retention OR persistence OR abandonment )
  AND
  ( rehabilitation OR therapy OR assistive )
)
```

### IEEE Xplore (draft)

```
("All Metadata":rehabilitation robot* OR exoskeleton OR "powered orthosis" OR "wearable robot")
AND
("All Metadata":adherence OR compliance OR engagement OR usage OR dropout OR abandonment)
```
*IEEE's query syntax is finicky; if the command search rejects the string, fall back to the
Advanced Search form with the same three concept groups and record the resulting URL in the log.*

### Semantic Scholar (API + web)

Web UI: `rehabilitation robot adherence`, `exoskeleton compliance rehabilitation`,
`robot-assisted therapy engagement dropout` — log each as a separate row.

API (bulk, for reproducibility): `GET https://api.semanticscholar.org/graph/v1/paper/search`
with `query="rehabilitation robotics adherence"`, paginated; fields
`title,abstract,year,externalIds,citationCount`. A small fetch helper can live in
`search/semantic_scholar_search.py` (optional, added when the search is actually run — not before).

### arXiv (draft)

```
(abs:"rehabilitation robot" OR abs:exoskeleton OR abs:"wearable robot" OR abs:orthosis)
AND
(abs:adherence OR abs:compliance OR abs:engagement OR abs:usage OR abs:dropout)
```
*Expect low yield (arXiv skews ML/control, not clinical adherence) — this source mainly catches
recent method preprints.*

### Google Scholar (supplementary)

`rehabilitation robot adherence OR compliance OR engagement` — screen the **first 100 results**
only (Scholar has no reproducible export or stable ordering); record the date, the query, and that
the cap was 100. Used chiefly for forward-citation chasing on key includes, not as a primary count.

---

## Pilot / calibration procedure

1. Run each draft string once. Record hits in `search-log.csv` with `run_type = pilot`.
2. Sanity-check against a small **seed set** of already-known relevant papers (list them in
   `search/seed-set.md` as you identify them): every seed that is indexed in a database *should*
   be returned by that database's string. A seed that is missed means the string is too narrow —
   widen Block B or relax a clause, and note the change here.
3. When recall (seeds found) and precision (manual scan of the first ~50 hits) are both acceptable,
   **freeze** the strings, bump this file to `v1.0`, and do the real runs with `run_type = final`.
4. Re-run all final searches on a single "search executed" date and record it; that date is the
   census point reported in the paper.

## Changelog

| Version | Date | Change |
|---|---|---|
| v0.1 | TBD (this commit) | Initial draft strings. Not yet piloted. |
| v0.1 (piloted) | 2026-08-13 | PubMed string piloted: **1099 hits**, no phrase warnings, recall 3/3 on PubMed-indexed seeds (`seed-set.md`, `search-log.csv`). Block C not needed at this volume. |
| **v1.0** | 2026-08-13 | **Frozen for execution.** PubMed is the calibrated **primary** string (recall 3/3, 1099 hits). Semantic Scholar / arXiv / Google Scholar treated as **supplementary** (relevance-ranked, not boolean; unauthenticated S2 API is rate-limited, so exact pilot counts are deferred and **not required** for calibration). This is the version the Phase A paper cites; superseding it = a new version + changelog row, not a silent edit. |
