# PRISMA flow — record counts

Live tracker for the PRISMA(-ScR) flow diagram. Fill the `n = TBD` values as each stage completes;
these numbers must reconcile with [`search/search-log.csv`](search/search-log.csv) and
[`screening/screening-template.csv`](screening/screening-template.csv). Nothing here is filled
until the corresponding step has actually been run.

## Identification

| Stage | Count |
|---|---|
| Records identified — PubMed/MEDLINE | **n = 1099** |
| Records identified — Scopus / WoS | n = TBD — *not run: no institutional access (run manually if access obtained)* |
| Records identified — IEEE Xplore | n = TBD — *not run: no institutional access* |
| Records identified — Semantic Scholar | n = TBD — *supplementary; unauthenticated API rate-limited (HTTP 429), deferred* |
| Records identified — arXiv | **n = 31** |
| Records identified — Google Scholar (first 100) | n = TBD — *manual step (no reproducible export/order)* |
| Records identified — snowballing (citation chasing) | n = TBD — *later stage, after includes exist* |
| **Total identified (sources run so far)** | **n = 1130** *(provisional: PubMed + arXiv)* |
| Duplicates removed | n = TBD — *finalised in Zotero; no shared identifiers between PubMed & arXiv sets* |
| **Records after dedup (→ screening)** | **n = TBD** *(provisional ≈ 1130, pending Zotero dedup)* |

> **Handoff to Zotero (desktop step).** The identifier sets are exported for import:
> [`search/pubmed-pmids-2026-08-16.txt`](search/pubmed-pmids-2026-08-16.txt) (1099 PMIDs — Zotero
> *Add Item by Identifier*) and [`search/arxiv-ids-2026-08-16.txt`](search/arxiv-ids-2026-08-16.txt)
> (31 arXiv IDs). Import → run Zotero *Duplicate Items* → record the real "Duplicates removed" and
> "after dedup" here. Totals stay provisional until that runs and any access-gated sources are added.

## Screening

| Stage | Count |
|---|---|
| Title/abstract screened | n = TBD |
| Excluded at T/A | n = TBD |
| Full texts sought | n = TBD |
| Full texts not retrieved (E5) | n = TBD |
| Full texts assessed | n = TBD |
| Excluded at full text (by reason code) | n = TBD |
| — E1 no-robotics | n = TBD |
| — E2 no-adherence | n = TBD |
| — E3 wrong-context | n = TBD |
| — E4 not-research | n = TBD |
| — E6 language | n = TBD |
| — E7 duplicate | n = TBD |

## Included

| Stage | Count |
|---|---|
| **Studies included in the review** | **n = TBD** |

---

**Intra-rater reliability** (solo-reviewer 10% re-screen, protocol §6): Cohen's κ = TBD
(re-screen date TBD).

**Search executed (census date):** 2026-08-16 — PubMed (primary, frozen v1.0 string) + arXiv
(supplementary). Scopus/WoS, IEEE, Semantic Scholar, Google Scholar, and snowballing still pending
(see per-source notes above). Numbers reconcile with `search/search-log.csv` (`run_type = final`).
