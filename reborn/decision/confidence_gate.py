"""Confidence gating: reduces or blocks assist under uncertainty, never increases it."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    assist_scale: float  # in [0, 1] — a ceiling, not a target


class ConfidenceGate:
    """Maps a confidence score to an assist ceiling.

    Downstream consumers must still apply `reborn.safety.limits` on top of
    `assist_scale` — this gate expresses "how much of the requested assist is
    trustworthy," not a hard safety bound.
    """

    def __init__(self, low_threshold: float = 0.4, high_threshold: float = 0.7) -> None:
        if not 0.0 <= low_threshold <= high_threshold <= 1.0:
            raise ValueError("expected 0 <= low_threshold <= high_threshold <= 1")
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold

    def evaluate(self, confidence: float) -> GateResult:
        if confidence < self.low_threshold:
            return GateResult(allowed=False, assist_scale=0.0)
        if confidence < self.high_threshold:
            span = self.high_threshold - self.low_threshold
            scale = (confidence - self.low_threshold) / span
            return GateResult(allowed=True, assist_scale=scale)
        return GateResult(allowed=True, assist_scale=1.0)
