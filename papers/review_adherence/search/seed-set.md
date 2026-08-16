# Seed set — known-relevant papers for search calibration

A small set of papers already known to be relevant, used to test search-string recall
(`search-strategy.md` §pilot). Every indexed seed should be returned by the corresponding
database's string; a missed seed means the string is too narrow.

> This is **not** part of the review results and does **not** pre-decide inclusion. It is a
> calibration instrument. Add seeds as encountered; cite only papers actually verified
> (no fabricated references).

**Verification:** metadata below confirmed against Crossref (`api.crossref.org/works/<doi>`) and,
for seed 4, the PMC record, on **2026-08-13**. The "Found by" column records the **pilot recall
result** (2026-08-13, logged in `search-log.csv`): the PubMed draft string returns all three
PubMed-indexed seeds (2/3/4) when tested; seed 1 is not PubMed-indexed but is confirmed in Semantic
Scholar. **Recall on PubMed: 3/3.**

Seeds deliberately span the Block B synonym space so the pilot tests each: *adherence* (1),
*engagement* (2), *assist-as-needed / performance* (3), *usage* (4). Coverage note: none of the
four directly links adherence to the *appropriateness/trust/safety* of assistance — consistent with
RQ4 being the suspected gap, not a defect of the seed set.

| # | Citation (author, year, title, venue) | DOI | Why it's a seed | Found by (databases) |
|---|---|---|---|---|
| 1 | Auger C., Boisvert A.-C., Jobin K., Michaud F. (2024). *Perception of the usefulness of socially assistive robots for adherence to home-based rehabilitation exercises for persons with chronic neurological conditions.* Proc. 17th Int. Conf. on PErvasive Technologies Related to Assistive Environments (PETRA '24), ACM. | 10.1145/3652037.3663930 | RQ1/RQ3 — adherence as concept + perceived usefulness as an influencing factor; tests Block B term *adherence*. | Semantic Scholar (indexed; not in PubMed) |
| 2 | Blank A. A., French J. A., Pehlivan A. U., O'Malley M. K. (2014). *Current Trends in Robot-Assisted Upper-Limb Stroke Rehabilitation: Promoting Patient Engagement in Therapy.* Current Physical Medicine and Rehabilitation Reports. | 10.1007/s40141-014-0056-z | RQ3/RQ1 — review of engagement in robot-assisted rehab; tests Block B near-synonym *engagement*. | PubMed (PMID 26005600) |
| 3 | Ödemiş E., Baysal C. V., İnci M. (2025). *Patient performance assessment methods for upper extremity rehabilitation in assist-as-needed therapy strategies: a comprehensive review.* Medical & Biological Engineering & Computing. | 10.1007/s11517-025-03315-z | RQ2/RQ3 — measurement of patient performance under assist-as-needed; tests the assistance-strategy angle. | PubMed (PMID 39918767) |
| 4 | Sivan M., Gallagher J., Makower S., Keeling D., Bhakta B., O'Connor R. J., Levesley M. (2014). *Home-based Computer Assisted Arm Rehabilitation (hCAAR) robotic device for upper limb exercise after stroke: results of a feasibility study in home setting.* Journal of NeuroEngineering and Rehabilitation. | 10.1186/1743-0003-11-163 | RQ2 — primary feasibility study reporting device **usage time** as an adherence metric; tests Block B term *usage*. | PubMed (PMID 25495889) |

## Changelog

| Date | Change |
|---|---|
| 2026-08-13 | First four seeds added and verified (Crossref/PMC). Spans adherence/engagement/assist-as-needed/usage across RQ1–RQ3. |
| 2026-08-13 | Pilot recall run: PubMed draft string returns seeds 2/3/4 (3/3 indexed); seed 1 confirmed in Semantic Scholar. See `search-log.csv`. |
