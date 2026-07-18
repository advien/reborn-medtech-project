# Inclusion / exclusion criteria & reason codes

Operational version of [`../protocol.md`](../protocol.md) §3, for use during screening. Applied in
two stages: **T/A** (title + abstract) then **FT** (full text). At full-text stage, every excluded
record gets exactly **one primary reason code** (the first that applies, in the order below).

## Inclusion (must meet all)

- **I1 — Context:** rehabilitation robotics, robot-assisted therapy, powered/assistive orthosis,
  or exoskeleton used with human users.
- **I2 — Concept:** substantively addresses adherence / compliance / engagement / usage / dropout
  as a definition, measurement, influencing factor, or outcome (not a passing mention).
- **I3 — Type:** primary study, review, or methods/position paper with extractable content.

## Exclusion reason codes

| Code | Meaning |
|---|---|
| **E1 — no-robotics** | No robotic/orthotic device (e.g. conventional therapy only), and not used as a comparator to one. |
| **E2 — no-adherence** | Device present but adherence/usage/engagement/dropout not addressed beyond a passing mention. |
| **E3 — wrong-context** | Exoskeleton/robot outside rehabilitation (industrial, military, performance augmentation). |
| **E4 — not-research** | Editorial, news, patent, abstract-only with no extractable data. |
| **E5 — no-fulltext** | Full text not retrievable. |
| **E6 — language** | Not in English (recorded, excluded at this stage). |
| **E7 — duplicate** | Duplicate of an already-screened record missed by automated dedup. |

## Screening decisions

- `include` — passes to the next stage / into extraction.
- `exclude` — record the reason code.
- `maybe` — only allowed at T/A stage; forces retrieval of full text for an FT decision. No
  `maybe` may survive into the final set.

## Solo-reviewer consistency check

Per protocol §6: after a ≥1-week gap, re-screen a random 10% of T/A records blind to the first
decision, and report Cohen's κ between the two passes as the intra-rater reliability figure. Log
the re-screen in a separate copy of the screening sheet (`screening-recheck.csv`) so the original
decisions are not overwritten.
