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


def waveform_length(x: np.ndarray) -> float:
    """Cumulative absolute change across the window — amplitude *and* frequency.

    Part of the Hudgins time-domain set. Unnormalised, so its scale follows the
    signal's: on Ninapro DB6 (samples of order 1e-5) it lands orders of magnitude
    below `zcr`, which is a fraction. Standardise features before handing them to
    a distance-based model.
    """
    if len(x) < 2:
        return 0.0
    return float(np.sum(np.abs(np.diff(x))))


def slope_sign_changes(x: np.ndarray, threshold: float = 0.0) -> float:
    """Fraction of samples where the slope reverses — a frequency proxy robust to DC.

    The rest of the Hudgins set. `threshold` suppresses reversals driven by noise
    rather than by the signal.
    """
    if len(x) < 3:
        return 0.0
    slope = np.diff(x)
    reversed_sign = (slope[:-1] * slope[1:]) < 0
    significant = np.maximum(np.abs(slope[:-1]), np.abs(slope[1:])) > threshold
    return float(np.sum(reversed_sign & significant)) / (len(x) - 2)


def extract_features(x: np.ndarray) -> dict[str, float]:
    """The Hudgins time-domain set.

    `reborn.data.features` computes these in batch over a whole `WindowSet`; the
    definitions here stay the single source of truth, and a test binds the two.
    """
    return {
        "rms": rms(x),
        "mav": mean_absolute_value(x),
        "zcr": zero_crossing_rate(x),
        "wl": waveform_length(x),
        "ssc": slope_sign_changes(x),
    }
