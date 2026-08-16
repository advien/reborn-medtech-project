# Reborn: architecture / position paper

**Phase D** (docs/roadmap.md). Safety-first, human-in-the-loop active elbow
orthosis: sensing → QC → decision logic → actuation → safety → feedback, and
the role (and deliberate non-role) of ML — advisory, bounded, never the
controller or safety authority.

Per the roadmap, this paper is already largely drafted in spirit — see
`docs/research/research-context.md` (the core thesis: contribution is *architectural
rather than algorithmic* — a system organization where confidence, decision
making, and safety are explicitly separated), `docs/architecture.md`,
`docs/safety.md`, and `docs/mapping-to-cv.md` for the existing source material
to draw from. It should also incorporate concrete results from phases B and C
once those exist, and cite the code/data git tag those results came from.

Note (`docs/research/research-context.md`, sections 6–7): novelty of the architectural
framing is an **open question** to be settled by the phase-A literature review,
not an assumption — this paper must not claim novelty in any individual
component.

Concrete phase-B input already in hand: [`../drift_personalization/synthesis-two-monitors.md`](../drift_personalization/synthesis-two-monitors.md)
gives a measured basis for a **two-monitor** safety architecture — input-quality
monitoring (`sensing`/`ml.anomaly`) and decision-drift monitoring (a label-free
confidence/disagreement signal in `decision`) as separate, non-redundant layers
feeding the confidence gate. DB6 shows a distinct failure mode for each that its
counterpart is blind to (contact fault vs. concept drift).

Target venues: workshops at ICRA / IROS / EMBC (see docs/roadmap.md).

Not started as a standalone manuscript.
