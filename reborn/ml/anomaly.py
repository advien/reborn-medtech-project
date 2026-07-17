"""Invalid-signal / anomaly detection — interface stub.

TODO(phase B, docs/roadmap.md): a direct contribution to the safety layer,
catching bad contact/dropout/saturation patterns beyond
reborn.sensing.emg_qc's simple heuristics.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AnomalyScore:
    is_anomalous: bool
    score: float


class AnomalyDetector:
    def score(self, features: np.ndarray) -> AnomalyScore:
        raise NotImplementedError("Phase B work — no trained model yet. See docs/roadmap.md.")
