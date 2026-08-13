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


# --------------------------------------------------------------------------- #
# Fault-sensitive features — for the advisory anomaly detector, NOT intent.
#
# The Hudgins set above describes *muscle activity* and is the right input for
# intent classification. Signal *faults*, though, show up in the spectrum and in
# waveform shape more than in amplitude, so `reborn.ml.anomaly` needs a richer
# view. These stay separate from `extract_features` so the intent feature set is
# not polluted with descriptors it does not want. Measured on real DB6 (phase
# B3a): adding these lifts the advisory detector's saturation/clipping detection
# to ~100%. A short, moderate `noise_burst` stays hard — a localized transient is
# within the natural window-to-window variation of real EMG, a floor set by the
# window granularity of the detector, not by the feature choice.
# --------------------------------------------------------------------------- #


def _rfft_power(x: np.ndarray, sample_rate: float) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x, dtype=float)
    x = x - x.mean()  # drop DC so it does not dominate the low bin
    freqs = np.fft.rfftfreq(len(x), d=1.0 / sample_rate)
    power = np.abs(np.fft.rfft(x)) ** 2
    return freqs, power


def mean_frequency(x: np.ndarray, sample_rate: float) -> float:
    """Power-weighted mean frequency (Hz); rises with broadband/high-frequency content."""
    freqs, power = _rfft_power(x, sample_rate)
    total = float(power.sum())
    return float((freqs * power).sum() / total) if total > 0 else 0.0


def high_frequency_ratio(x: np.ndarray, sample_rate: float, cutoff_hz: float = 150.0) -> float:
    """Fraction of spectral power at or above `cutoff_hz` — a broadband-noise tell."""
    freqs, power = _rfft_power(x, sample_rate)
    total = float(power.sum())
    return float(power[freqs >= cutoff_hz].sum() / total) if total > 0 else 0.0


def kurtosis(x: np.ndarray) -> float:
    """Fourth standardized moment; high for impulsive / heavy-tailed windows."""
    x = np.asarray(x, dtype=float)
    sd = float(x.std())
    if sd == 0.0:
        return 0.0
    return float(np.mean(((x - x.mean()) / sd) ** 4))


def crest_factor(x: np.ndarray) -> float:
    """Peak-to-RMS ratio; high when a short transient dominates the window."""
    r = rms(x)
    return float(np.max(np.abs(x)) / r) if r > 0 else 0.0


def subwindow_rms_ratio(x: np.ndarray, n_subwindows: int = 10) -> float:
    """max short-time RMS / overall RMS; flags energy concentrated in a burst.

    A whole-window RMS averages a localized transient away; comparing the loudest
    sub-window against the window as a whole keeps some of that locality.
    """
    x = np.asarray(x, dtype=float)
    n = (len(x) // n_subwindows) * n_subwindows
    if n < n_subwindows:
        return 1.0
    sub = x[:n].reshape(n_subwindows, -1)
    sub_rms = np.sqrt(np.mean(np.square(sub), axis=1))
    overall = rms(x)
    return float(sub_rms.max() / overall) if overall > 0 else 1.0


def anomaly_features(x: np.ndarray, sample_rate: float) -> dict[str, float]:
    """Feature vector for `reborn.ml.anomaly` — Hudgins set plus fault-sensitive
    spectral and impulse descriptors. See the section comment above."""
    return {
        **extract_features(x),
        "mnf": mean_frequency(x, sample_rate),
        "hfr": high_frequency_ratio(x, sample_rate),
        "kurt": kurtosis(x),
        "crest": crest_factor(x),
        "sw_rms": subwindow_rms_ratio(x),
    }
