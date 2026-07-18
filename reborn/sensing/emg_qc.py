"""EMG signal-quality checks: dropout and saturation detection.

These are deliberately simple heuristics — the direct ML contribution to this
(reborn.ml.anomaly, phase B) is meant to go beyond what these catch, not replace
them; the heuristics stay as a cheap, always-on first line of defense.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SignalQuality:
    valid: bool
    reason: str | None = None


def check_dropout(x: np.ndarray, flatline_std: float = 1e-6) -> SignalQuality:
    if float(np.std(x)) < flatline_std:
        return SignalQuality(valid=False, reason="dropout")
    return SignalQuality(valid=True)


def check_saturation(x: np.ndarray, limit: float = 1.0, max_fraction: float = 0.05) -> SignalQuality:
    saturated_fraction = float(np.mean(np.abs(x) >= limit))
    if saturated_fraction > max_fraction:
        return SignalQuality(valid=False, reason="saturation")
    return SignalQuality(valid=True)


def assess_quality(x: np.ndarray, saturation_limit: float = 1.0, flatline_std: float = 1e-6) -> SignalQuality:
    """Runs all quality checks, returning the first failure found."""
    dropout = check_dropout(x, flatline_std)
    if not dropout.valid:
        return dropout
    return check_saturation(x, saturation_limit)
