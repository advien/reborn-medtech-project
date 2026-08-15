"""Tests for the advisory anomaly detector (reborn.ml.anomaly).

The detector is fit on features from clean windows and must (a) leave clean
windows mostly un-flagged and (b) flag windows corrupted by known faults, at a
higher rate than clean ones. It is intentionally numpy-only so it runs in the
base install.
"""

from __future__ import annotations

import math

import numpy as np

from reborn.ml.anomaly import AdaptiveThreshold, AnomalyDetector
from reborn.sensing import corruption
from reborn.sensing.emg_qc import assess_quality
from reborn.sensing.features import extract_features


def _feature_row(x: np.ndarray) -> list[float]:
    f = extract_features(x)
    return [f["rms"], f["mav"], f["zcr"]]


def _clean_window(rng: np.random.Generator, n: int = 400) -> np.ndarray:
    return 0.1 * rng.standard_normal(n)


def _fit_on_clean(n_windows: int = 200, seed: int = 0) -> AnomalyDetector:
    rng = np.random.default_rng(seed)
    X = np.array([_feature_row(_clean_window(rng)) for _ in range(n_windows)])
    return AnomalyDetector(contamination=0.025).fit(X)


def test_fit_required_before_score():
    det = AnomalyDetector()
    assert not det.fitted
    try:
        det.score(np.zeros(3))
    except RuntimeError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected RuntimeError before fit()")


def test_clean_windows_mostly_pass():
    det = _fit_on_clean()
    rng = np.random.default_rng(999)  # unseen clean windows
    flags = [det.score(_feature_row(_clean_window(rng))).is_anomalous for _ in range(200)]
    # false-positive rate should be near the contamination level, allow headroom
    assert np.mean(flags) < 0.15


def test_corrupted_windows_flagged_more_than_clean():
    det = _fit_on_clean()
    rng = np.random.default_rng(7)

    clean_flags, corrupt_flags = [], []
    for _ in range(120):
        base = _clean_window(rng)
        clean_flags.append(det.score(_feature_row(base)).is_anomalous)
        bad = corruption.inject_saturation(base, limit=1.0, gain=50.0)
        corrupt_flags.append(det.score(_feature_row(bad)).is_anomalous)

    assert np.mean(corrupt_flags) > np.mean(clean_flags)
    assert np.mean(corrupt_flags) > 0.5  # saturation is an obvious deviation


def test_noise_burst_raises_anomaly_rate_above_clean():
    # noise_burst is the mode the deterministic QC deliberately doesn't name;
    # the advisory detector should still flag it more often than clean windows.
    det = _fit_on_clean()
    rng = np.random.default_rng(11)
    clean_flags, burst_flags = [], []
    for _ in range(150):
        base = _clean_window(rng)
        clean_flags.append(det.score(_feature_row(base)).is_anomalous)
        bad = corruption.inject_noise_burst(base, amplitude=0.6, start=0.4, length=0.3)
        burst_flags.append(det.score(_feature_row(bad)).is_anomalous)
    assert np.mean(burst_flags) > np.mean(clean_flags)


def test_heldout_calibration_holds_false_positive_rate():
    # Small training set, many features: the covariance over-fits, so a threshold
    # read off the training set under-counts false positives on unseen windows.
    # A held-out calibration set should pull the realised rate back to ~contamination.
    rng = np.random.default_rng(3)
    dim, contam = 8, 0.05
    train = rng.standard_normal((120, dim))
    calib = rng.standard_normal((1500, dim))
    test = rng.standard_normal((3000, dim))  # unseen clean windows

    naive = AnomalyDetector(contamination=contam).fit(train)
    calibrated = AnomalyDetector(contamination=contam).fit(train, calibration=calib)

    fp_naive = np.mean([naive.score(w).is_anomalous for w in test])
    fp_calibrated = np.mean([calibrated.score(w).is_anomalous for w in test])

    # calibrated rate lands near the target; the naive one overshoots it
    assert abs(fp_calibrated - contam) < abs(fp_naive - contam)
    assert fp_calibrated < 0.10


def test_calibration_feature_count_must_match():
    rng = np.random.default_rng(4)
    train = rng.standard_normal((50, 5))
    bad_calib = rng.standard_normal((50, 3))
    try:
        AnomalyDetector().fit(train, calibration=bad_calib)
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected ValueError on mismatched calibration width")


def test_distance_matches_score_and_shapes():
    det = _fit_on_clean()
    rng = np.random.default_rng(5)
    row = _feature_row(_clean_window(rng))
    # 1D -> float, and equals the score's distance
    d1 = det.distance(np.asarray(row))
    assert isinstance(d1, float)
    assert abs(d1 - det.score(row).score) < 1e-9
    # 2D -> array, one distance per row
    batch = np.array([_feature_row(_clean_window(rng)) for _ in range(10)])
    d2 = det.distance(batch)
    assert d2.shape == (10,) and np.all(np.isfinite(d2))


def test_score_is_finite_and_nonnegative():
    det = _fit_on_clean()
    s = det.score(_feature_row(np.ones(400)))
    assert np.isfinite(s.score) and s.score >= 0.0


def test_adaptive_threshold_warmup_returns_fallback():
    rng = np.random.default_rng(0)
    at = AdaptiveThreshold(contamination=0.025, window=1000, min_samples=200, fallback=7.0)
    assert not at.ready
    assert at.value == 7.0  # fallback until warmed up
    assert at.flags(8.0) and not at.flags(6.0)
    at.update(rng.gamma(5.0, 1.0, size=500))
    assert at.ready
    assert math.isfinite(at.value) and at.value != 7.0  # now data-driven


def test_adaptive_threshold_reset_clears_buffer():
    at = AdaptiveThreshold(contamination=0.05, window=100, min_samples=10)
    at.update(np.ones(50))
    assert at.ready
    at.reset()
    assert not at.ready


def test_adaptive_threshold_holds_false_positive_under_drift():
    # Distances drift upward session to session; a fixed threshold calibrated on
    # session 0 flags ever more, while a per-session adaptive threshold holds the
    # rate at target. This is the notebook-03 result in miniature.
    rng = np.random.default_rng(1)
    contam = 0.025

    def session(k, n=4000):
        return (1.0 + 0.3 * k) * rng.gamma(shape=5.0, scale=1.0, size=n)

    fixed_thr = float(np.quantile(session(0), 1 - contam))
    at = AdaptiveThreshold(contamination=contam, window=4000, min_samples=200)

    fixed_fps, adaptive_fps = [], []
    for k in range(6):
        d = session(k)
        half = len(d) // 2
        fixed_fps.append(float(np.mean(d[half:] > fixed_thr)))
        at.reset()
        at.update(d[:half])
        adaptive_fps.append(float(np.mean([at.flags(x) for x in d[half:]])))

    assert np.mean(adaptive_fps) < np.mean(fixed_fps)
    assert abs(np.mean(adaptive_fps) - contam) < 0.02  # adaptive stays at target
    assert max(fixed_fps) > 0.10  # fixed blows up on the drifted sessions


def test_floor_is_authoritative_advisor_only_sees_clean():
    # The deterministic floor decides first; a window it rejects never feeds the
    # advisory threshold, so adaptation can never relax a hard safety check.
    det = _fit_on_clean()
    at = AdaptiveThreshold(contamination=0.05, window=100, min_samples=5)
    rng = np.random.default_rng(2)
    windows = [_clean_window(rng) for _ in range(20)] + [np.zeros(400)]  # last: dropout

    for w in windows:
        if not assess_quality(w).valid:
            continue  # floor rejects; the advisor is not consulted or updated
        at.update(det.distance(_feature_row(w)))

    assert len(at._buffer) == 20  # the dropout window did not enter the advisory


def test_singular_features_do_not_crash():
    # constant features across windows -> singular covariance without the ridge
    X = np.ones((50, 3))
    det = AnomalyDetector().fit(X)
    assert det.fitted
    assert np.isfinite(det.score(np.ones(3)).score)
