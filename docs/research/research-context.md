# Reborn — Research Context

## Purpose

This document captures the current research hypothesis behind the Reborn project.
It is **not** a statement that the ideas below are novel.
Instead, it defines the questions that should be answered through a systematic literature review before making any novelty claims.

The objective is to distinguish between:
- established knowledge,
- existing research directions,
- open research problems,
- and potential contributions of Reborn.

---

# 1. What does Reborn actually study?

At first glance, Reborn appears to study:
- EMG
- IMU
- Signal fusion
- Machine Learning

However, these are **not** the research object.
They are engineering tools.

Likewise:
- the orthosis is a tool,
- machine learning is a tool,
- sensing is a tool.

The actual research object is the **decision-making process of an assistive robotic system under uncertainty.**

An early formulation of the central research question is:

> **How should an assistive robotic system determine the appropriate level of assistance under uncertain sensing conditions?**

Earlier formulations included:

> How should an assistive robotic system decide when not to help?

This remains an important sub-question, but it may be better understood as one possible outcome of a broader assistance policy rather than the primary objective.

---

# 2. Why is this question interesting?

Many assistive robotics projects primarily optimize:
- prediction accuracy,
- gesture recognition,
- EMG classification,
- control precision.

Reborn is interested in a different problem.

Instead of asking:

> "How can assistance become more accurate?"

the project asks:

> **How can an assistive system understand the limits of its own confidence?**

or, more generally,

> **How should uncertainty influence assistive control?**

This shifts the focus from maximizing assistance toward determining **appropriate assistance**.

---

# 3. Why is "not helping" sometimes the safest decision?

The goal of an orthosis is to compensate for lost function.
However, real-world interaction introduces situations where assistance may become unsafe or counterproductive.

Examples include:

## Situation A — Assistance is appropriate
- User intends to flex the elbow.
- System confidence is high.
- Assistance is provided.

This represents the desired operating mode.

---

## Situation B — False intention
Examples:
- electrode displacement
- EMG noise
- motion artefacts

The system incorrectly concludes that the user intends to move.
Providing assistance here may cause unexpected movement and potentially unsafe interaction.

---

## Situation C — Assistance is unnecessary
The user has recovered sufficient function to complete the movement independently.
Continuous maximal assistance may:
- reduce muscle activation,
- reduce active participation,
- slow motor learning during rehabilitation.

Modern rehabilitation literature often discusses **assist-as-needed**, emphasizing adaptive rather than constant assistance.

---

Therefore, the real engineering problem is not simply:

> "Help or not help?"

Instead, it becomes:

> **When, how much, and with what confidence should assistance be provided?**

---

# 4. What do the notebooks investigate?

The public notebook track is a deliberately bounded three-step progression. All three are
**offline, pilot-scale** evidence on public data (Ninapro DB6, two subjects); none validates a
device, a controller, real-time operation, or a safe assistance threshold. Together they reach
offline evidence about *abstention* — the closest current public artifact to the question in §1.

---

## [Notebook 01 — Signal trust](../../notebooks/01_signal_trust.ipynb)

Question:

> Can the input signal be trusted enough to enter a decision pipeline?

Focus:
- deterministic signal-quality checks and per-session rejection
- advisory anomaly detection against calibrated injected faults
- what a one-class monitor actually models (activity composition vs. signal health)
- a per-session adaptive threshold for the advisory layer, above a fixed deterministic floor

---

## [Notebook 02 — Confidence under shift](../../notebooks/02_confidence_under_shift.ipynb)

Question:

> Does the probability stay honest when conditions change?

Focus:
- binary rest-vs-movement as the primary task; multi-class only as a 2-channel floor
- leakage-aware protocols (within-session by repetition, cross-session, cross-subject pilot,
  shuffle control)
- discrimination and probability quality (ECE, Brier, NLL) each on its own scale
- reliability diagrams and per-split variability

---

## [Notebook 03 — When not to help](../../notebooks/03_when_not_to_help.ipynb)

Question:

> When the system cannot trust its evidence, what warns it, and what does refusing cost?

Focus:
- input monitors (QC, anomaly) vs. decision monitors (confidence, disagreement, class share)
- illustrative failure cases — existence evidence, not coverage
- an explicit confidence rejector: risk–coverage and unsafe-assist vs. availability trade-offs

---

## Deferred: motion sensing and multimodal evidence

Two further questions from the original plan are **deferred, not abandoned**, pending a dataset
with synchronised motion data; they live in [`notebooks/future/`](../../notebooks/future/README.md):

- *When does observed motion disagree with human intent?* (IMU baselines)
- *Does EMG + IMU fusion improve confidence estimation rather than prediction accuracy?*

The system architecture in `docs/architecture.md` still describes EMG + IMU sensing; that is the
intended future system, unchanged by the notebook track's current scope.

---

# 5. Expected outcomes

The objective is **not** to obtain:
- maximum accuracy,
- highest F1-score,
- a new classifier.

Instead, Reborn aims to produce:

## 5.1 Assistance policy
A systematic policy describing:
- when assistance should increase,
- decrease,
- remain passive,
- or stop.

---

## 5.2 Confidence model
Not necessarily ML-based.
Rather:
a representation of when the system should consider its own decision reliable enough for physical interaction.

---

## 5.3 Failure taxonomy
A structured understanding of failure modes.
Examples include:
- EMG drift
- electrode displacement
- passive motion
- conflicting sensor information
- user fatigue
- signal degradation

---

## 5.4 Architecture validation
Validation of the complete system architecture rather than validation of an isolated algorithm.

---

# 6. Existing research (known areas)

The following areas are already active research topics:
- confidence estimation
- uncertainty-aware robotics
- EMG fusion
- assistive robotics
- shared control
- human-in-the-loop robotics

Therefore, Reborn should **not** assume novelty in any individual component.

---

# 7. Possible research contribution

The current working hypothesis is that the potential contribution of Reborn is **architectural rather than algorithmic**.

Working concept:

> **Safety-first confidence architecture for assistive robotics.**

The hypothesis is not:

> "a new ML model"

Instead:

> "a system organization in which confidence, decision making, and safety are explicitly separated."

Current architecture:

```text
Human
  ↓
Sensors
  ↓
Signal Quality
  ↓
Decision
  ↓
Safety
  ↓
Actuation
  ↓
Human
```

rather than

```text
Sensors
  ↓
Machine Learning
  ↓
Robot
  ↓
Human
```

Whether this architectural framing is genuinely new remains an open research question.
(See [`architecture.md`](../architecture.md) for how this maps onto the implemented package;
the position paper built on this thesis lives in the private research repository.)

---

# 8. Working design philosophy

Current working statement:

> **The primary objective of an assistive robotic system is not to maximize assistance. It is to maximize appropriate assistance.**

This statement is currently considered a **research hypothesis**, not a validated conclusion.

---

# 9. Open research questions

## Human Intent
How can an assistive system estimate human intent under noisy and uncertain conditions?

---

## Signal Reliability
Which properties of EMG and IMU indicate that they should not be trusted for control?

---

## Signal Fusion
Does combining EMG and IMU improve confidence estimation rather than raw prediction accuracy?

---

## Confidence
How should confidence be represented in assistive robotic systems?

---

## Decision Making
How should uncertainty influence assistive control decisions?

---

## Assistance Policy
How should an assistive robotic system determine the appropriate level of assistance?

---

## Shared Control
How should control authority be shared between the user and the robotic system?

---

## Safety
Which safety policies provide predictable behavior under uncertain sensing conditions?

---

## Failure Modes
Which signal degradation scenarios are most critical?

---

## Human Adaptation
How does user adaptation influence long-term assistive control?

---

## Architecture
Which system architecture best integrates sensing, confidence estimation, decision logic, and safety?

---

## Machine Learning
Where should machine learning be positioned within a safety-critical assistive robotic system?

---

## Explainability
How can assistive systems communicate uncertainty to users?

---

## Validation
Which experiments demonstrate safe behavior more effectively than prediction metrics alone?

---

# 10. Literature review strategy

Rather than searching broadly for orthosis papers, the review should be organized around research themes.

| Area | Goal |
|------|------|
| Assist-as-needed | Existing assistance policies |
| Shared control | Human–robot authority allocation |
| EMG reliability | Signal limitations |
| IMU reliability | Kinematic limitations |
| Confidence estimation | Existing confidence models |
| Uncertainty-aware robotics | Decision under uncertainty |
| Safety-critical robotics | Safety architectures |
| Human adaptation | User learning and co-adaptation |
| Explainable assistive robotics | Communicating uncertainty |

---

# 11. Current research priority

Before implementing additional algorithms or expanding the software stack, answer the following question through literature review:

> **Which problems in assistive robotics have already been solved, which remain open, and where can Reborn provide a meaningful contribution?**

Only after answering this question should claims about novelty or research contribution be considered.
