"""Invalid-signal / anomaly detection — advisory, bounded (phase B).

A one-class detector: it learns what *clean* EMG feature vectors look like and
scores how far a new window deviates. Unlike the fixed heuristics in
`reborn.sensing.emg_qc`, it has no per-mode rule — it flags "this doesn't look
like the normal signal I was fit on", catching bad-contact / degradation patterns
that no single threshold names.

Position in the architecture (invariants in CLAUDE.md):

* **Advisory only.** Output is a score + boolean, consumed through
  `reborn.decision.confidence_gate`, never wired to actuator commands and never
  overriding `reborn.safety`. Low confidence must *reduce* assist.
* **Bounded.** No hidden state, deterministic given the fit; `score` is a finite
  Mahalanobis distance.

Implementation is numpy-only (no sklearn/torch), so it runs and is tested in the
base install. Heavier learned backends (IsolationForest, autoencoder) trained on
real Ninapro windows are the phase-B upgrade — they slot behind this same
`fit`/`score` interface.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AnomalyScore:
    is_anomalous: bool
    score: float


class AnomalyDetector:
    """One-class Mahalanobis-distance detector fit on clean feature windows.

    Parameters
    ----------
    contamination:
        Expected fraction of the *training* set allowed above threshold. The
        decision threshold is the corresponding quantile of training distances,
        so a clean training set yields few false positives by construction.
    ridge:
        Diagonal regularisation added to the covariance before inversion, so the
        detector is well-defined for collinear or low-variance features.
    """

    def __init__(self, contamination: float = 0.025, ridge: float = 1e-6) -> None:
        if not 0.0 < contamination < 1.0:
            raise ValueError("contamination must be in (0, 1)")
        self.contamination = contamination
        self.ridge = ridge
        self._mean: np.ndarray | None = None
        self._inv_cov: np.ndarray | None = None
        self._threshold: float | None = None

    @property
    def fitted(self) -> bool:
        return self._threshold is not None

    @property
    def threshold(self) -> float | None:
        """Decision threshold on the Mahalanobis distance (None until fit)."""
        return self._threshold

    def fit(
        self, features: np.ndarray, calibration: np.ndarray | None = None
    ) -> "AnomalyDetector":
        """Fit on clean feature vectors, shape (n_windows, n_features).

        Args:
            features: clean windows used to estimate the mean and covariance.
            calibration: optional *separate* clean set. If given, the flag
                threshold is the `contamination` quantile of *its* distances
                rather than the training set's. This matters whenever features
                outnumber training rows only modestly: the sample covariance
                hugs the data it was fit on, so training distances understate
                the spread of unseen windows and the realised false-positive
                rate runs above `contamination`. A held-out calibration set
                sets the threshold against distances the covariance did not fit,
                so the false-positive target holds on new data.
        """
        X = np.asarray(features, dtype=float)
        if X.ndim != 2 or X.shape[0] < 2:
            raise ValueError("features must be 2D with at least 2 rows")
        self._mean = X.mean(axis=0)
        cov = np.cov(X, rowvar=False)
        cov = np.atleast_2d(cov) + self.ridge * np.eye(X.shape[1])
        self._inv_cov = np.linalg.inv(cov)

        if calibration is not None:
            cal = np.asarray(calibration, dtype=float)
            if cal.ndim != 2 or cal.shape[1] != X.shape[1]:
                raise ValueError("calibration must be 2D with the same feature count as `features`")
            threshold_scores = self._mahalanobis(cal)
        else:
            threshold_scores = self._mahalanobis(X)
        self._threshold = float(np.quantile(threshold_scores, 1.0 - self.contamination))
        return self

    def score(self, features: np.ndarray) -> AnomalyScore:
        """Score a single feature vector, shape (n_features,)."""
        if not self.fitted:
            raise RuntimeError("AnomalyDetector.score called before fit()")
        v = np.asarray(features, dtype=float).reshape(1, -1)
        d = float(self._mahalanobis(v)[0])
        return AnomalyScore(is_anomalous=d > self._threshold, score=d)

    def distance(self, features: np.ndarray) -> float | np.ndarray:
        """Raw Mahalanobis distance(s) to the fitted centre, without thresholding.

        A 1D input returns a float; a 2D `(n, n_features)` input returns an array.
        Exposed so callers can apply their own threshold — e.g. a per-session or
        rolling adaptive threshold that tracks drift — while the fit (mean and
        covariance) stays fixed. The threshold is a policy choice; the distance is
        the measurement.
        """
        if self._mean is None or self._inv_cov is None:
            raise RuntimeError("AnomalyDetector.distance called before fit()")
        X = np.asarray(features, dtype=float)
        single = X.ndim == 1
        d = self._mahalanobis(X.reshape(1, -1) if single else X)
        return float(d[0]) if single else d

    def _mahalanobis(self, X: np.ndarray) -> np.ndarray:
        assert self._mean is not None and self._inv_cov is not None
        delta = X - self._mean
        # sqrt of the quadratic form delta @ inv_cov @ delta.T, per row
        return np.sqrt(np.einsum("ij,jk,ik->i", delta, self._inv_cov, delta))


class AdaptiveThreshold:
    """Advisory flag threshold that tracks drift by recalibrating on recent clean
    window distances (phase B3c).

    The `AnomalyDetector` fit (mean, covariance) stays fixed; only the *threshold*
    on its distance moves, following the wearer's current baseline. Notebook 03
    measured why: a single fixed threshold calibrated on one session runs the
    clean false-positive rate to double digits on later sessions as the signal
    drifts, while a per-session threshold holds it at target.

    **This is advisory and sits above a fixed floor — that is the whole safety
    argument (CLAUDE.md invariant 2).** Feed it only the distances of windows that
    already passed the deterministic gate (`reborn.sensing.emg_qc.assess_quality`),
    so it never relaxes a hard safety check; it only adjusts the advisory
    detector's sensitivity. The deterministic floor — not this threshold — is what
    catches the named faults (dropout, saturation, …). A slow *uniform* degradation
    that this threshold might adapt to is still caught there; a heterogeneous one
    (e.g. DB6 session d04) stays visible because recalibrating on early clean
    windows cannot normalise a fault that arrives later in the session.

    Usage — per session: `reset()` at each session boundary, `update(distances)`
    with that session's early clean-window distances, then `flags(distance)` on the
    rest. Or leave it rolling (never reset) for a continuous trailing window.

    Args:
        contamination: target clean false-positive rate; the threshold is the
            `1 - contamination` quantile of the buffered clean distances.
        window: trailing buffer size (most recent clean distances kept).
        min_samples: distances required before the buffer is trusted; until then
            `value` returns `fallback`.
        fallback: threshold used during warm-up. Defaults to `+inf` (the advisor
            stays silent until it has a baseline — safe because the deterministic
            floor is already active). Pass the detector's fixed global threshold
            to fall back to fixed behaviour instead.
    """

    def __init__(
        self,
        contamination: float = 0.025,
        window: int = 4000,
        min_samples: int = 200,
        fallback: float = math.inf,
    ) -> None:
        if not 0.0 < contamination < 1.0:
            raise ValueError("contamination must be in (0, 1)")
        if min_samples < 1 or window < min_samples:
            raise ValueError("require 1 <= min_samples <= window")
        self.contamination = contamination
        self.window = window
        self.min_samples = min_samples
        self.fallback = fallback
        self._buffer: deque[float] = deque(maxlen=window)

    def reset(self) -> None:
        """Clear the buffer — call at a session boundary for per-session adaptation."""
        self._buffer.clear()

    def update(self, distances: float | np.ndarray) -> "AdaptiveThreshold":
        """Add clean-window distance(s) to the trailing buffer."""
        arr = np.atleast_1d(np.asarray(distances, dtype=float)).ravel()
        self._buffer.extend(float(d) for d in arr)
        return self

    @property
    def ready(self) -> bool:
        return len(self._buffer) >= self.min_samples

    @property
    def value(self) -> float:
        """Current threshold: the quantile of buffered distances, or `fallback`
        until at least `min_samples` have been seen."""
        if not self.ready:
            return self.fallback
        return float(np.quantile(np.fromiter(self._buffer, dtype=float), 1.0 - self.contamination))

    def flags(self, distance: float) -> bool:
        """True if `distance` exceeds the current threshold (advisory anomaly)."""
        return float(distance) > self.value
