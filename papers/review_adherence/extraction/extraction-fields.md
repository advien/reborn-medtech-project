# Data-charting fields

Field definitions for [`extraction-template.csv`](extraction-template.csv). One row per **included**
study. Fields map to the review questions in [`../protocol.md`](../protocol.md) §2 so the synthesis
falls out of the chart directly.

| Field | RQ | Definition / allowed values |
|---|---|---|
| `record_id` | — | Matches the screening sheet record id (e.g. R0001). |
| `citation` | — | Author (year), short title, venue. |
| `doi_url` | — | DOI / arXiv id / stable URL. |
| `study_type` | — | RCT / cohort / cross-sectional / pilot / review / methods / position / other. |
| `population` | P | Condition & who: stroke, SCI, MS, orthopaedic, healthy, mixed; adult/paediatric. |
| `n_participants` | P | Sample size (blank if review/methods). |
| `device_type` | Context | End-effector robot / exoskeleton / powered orthosis / exosuit / other. |
| `body_region` | Context | Upper limb / lower limb / hand / elbow / trunk / other. |
| `setting` | Context | Clinic / lab / home / mixed. |
| `assistance_strategy` | RQ3 | Fixed / assist-as-needed / adaptive / EMG-triggered / resistive / not-stated. |
| `adherence_definition` | RQ1 | Verbatim or paraphrased definition of adherence/compliance/engagement used. |
| `adherence_metric` | RQ2 | How measured: session count, prescribed-vs-completed dose, active time, repetitions, self-report scale (name it), sensor-derived usage, dropout/attrition rate, other. |
| `metric_source` | RQ2 | Device-logged / self-report / therapist-recorded / mixed. |
| `factors_increase` | RQ3 | Reported factors associated with higher adherence. |
| `factors_decrease` | RQ3 | Reported factors associated with lower adherence / dropout. |
| `links_appropriateness` | RQ4 | Does it link adherence to *appropriateness* of assistance, trust, or safety? yes/no + one line. **The Reborn-relevant bridge field.** |
| `key_finding` | — | One-sentence takeaway. |
| `gap_noted` | RQ4 | Any gap/future-work the authors flag re: adherence measurement or influence. |
| `extractor` | — | Who charted it. |
| `extract_date` | — | Date. |
| `notes` | — | Anything else. |

**Charting discipline.** Chart only what the paper actually reports. Use `not-stated` rather than
inferring. Direct quotes for `adherence_definition` where short, in quotation marks.
