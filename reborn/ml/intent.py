"""Intent classification (flex / no-flex) — interface stub.

TODO(phase B, docs/roadmap.md): train and wire in a classifier on open EMG data
(Ninapro, EMG-EPN-612).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class IntentPrediction:
    intent: bool
    confidence: float


class IntentClassifier:
    def predict(self, features: np.ndarray) -> IntentPrediction:
        raise NotImplementedError("Phase B work — no trained model yet. See docs/roadmap.md.")
