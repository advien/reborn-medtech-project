"""Drift / few-shot personalization — interface stub.

TODO(phase B, docs/roadmap.md topic 7): cross-session/cross-subject adaptation
without long recalibration — flagged in the roadmap as the strongest
candidate publication for phase B.
"""

from __future__ import annotations

import numpy as np


class Personalizer:
    def adapt(self, calibration_features: np.ndarray, calibration_labels: np.ndarray) -> None:
        raise NotImplementedError("Phase B work — no trained model yet. See docs/roadmap.md.")
