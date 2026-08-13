"""Tests for the fault-sensitive features feeding reborn.ml.anomaly.

Each feature is checked for the property that makes it useful to the anomaly
detector: it must respond in the expected direction to the signal characteristic
it is meant to capture.
"""

from __future__ import annotations

import numpy as np

from reborn.sensing.features import (
    anomaly_features,
    crest_factor,
    extract_features,
    high_frequency_ratio,
    kurtosis,
    mean_frequency,
    subwindow_rms_ratio,
)

RATE = 1000.0


def _sine(freq: float, n: int = 400) -> np.ndarray:
    return np.sin(2 * np.pi * freq * np.arange(n) / RATE)


def test_mean_frequency_rises_with_frequency():
    assert mean_frequency(_sine(200), RATE) > mean_frequency(_sine(20), RATE)


def test_high_frequency_ratio_separates_hf_from_lf():
    assert high_frequency_ratio(_sine(300), RATE) > 0.8
    assert high_frequency_ratio(_sine(20), RATE) < 0.2


def test_kurtosis_higher_for_impulsive_signal():
    rng = np.random.default_rng(0)
    gaussian = rng.standard_normal(400)
    impulsive = np.zeros(400)
    impulsive[200] = 10.0  # a single spike
    assert kurtosis(impulsive) > kurtosis(gaussian)


def test_crest_factor_higher_with_a_transient():
    flat = np.ones(400) * 0.5
    spiky = np.ones(400) * 0.5
    spiky[100] = 20.0
    assert crest_factor(spiky) > crest_factor(flat)


def test_subwindow_rms_ratio_flags_localized_energy():
    rng = np.random.default_rng(1)
    uniform = 0.1 * rng.standard_normal(400)
    burst = 0.1 * rng.standard_normal(400)
    burst[180:220] += 2.0 * rng.standard_normal(40)  # energy concentrated in one sub-window
    assert subwindow_rms_ratio(burst) > subwindow_rms_ratio(uniform)


def test_anomaly_features_superset_of_hudgins():
    x = _sine(100)
    feats = anomaly_features(x, RATE)
    assert set(extract_features(x)) <= set(feats)
    assert {"mnf", "hfr", "kurt", "crest", "sw_rms"} <= set(feats)
    assert all(np.isfinite(v) for v in feats.values())


def test_features_finite_on_flat_signal():
    flat = np.zeros(400)
    feats = anomaly_features(flat, RATE)
    assert all(np.isfinite(v) for v in feats.values())
