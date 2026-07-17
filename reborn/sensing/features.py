"""Basic EMG time-domain features."""

from __future__ import annotations

import numpy as np


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x))))


def mean_absolute_value(x: np.ndarray) -> float:
    return float(np.mean(np.abs(x)))


def zero_crossing_rate(x: np.ndarray, threshold: float = 0.0) -> float:
    """Fraction of adjacent samples that cross zero with amplitude > threshold."""
    if len(x) < 2:
        return 0.0
    signs = np.sign(x)
    signs[signs == 0] = 1
    crossings = np.diff(signs) != 0
    above_threshold = np.abs(np.diff(x)) > threshold
    return float(np.sum(crossings & above_threshold)) / (len(x) - 1)


def extract_features(x: np.ndarray) -> dict[str, float]:
    return {
        "rms": rms(x),
        "mav": mean_absolute_value(x),
        "zcr": zero_crossing_rate(x),
    }
