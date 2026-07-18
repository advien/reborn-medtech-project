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

    def fit(self, features: np.ndarray) -> "AnomalyDetector":
        """Fit on clean feature vectors, shape (n_windows, n_features)."""
        X = np.asarray(features, dtype=float)
        if X.ndim != 2 or X.shape[0] < 2:
            raise ValueError("features must be 2D with at least 2 rows")
        self._mean = X.mean(axis=0)
        cov = np.cov(X, rowvar=False)
        cov = np.atleast_2d(cov) + self.ridge * np.eye(X.shape[1])
        self._inv_cov = np.linalg.inv(cov)
        train_scores = self._mahalanobis(X)
        self._threshold = float(np.quantile(train_scores, 1.0 - self.contamination))
        return self

    def score(self, features: np.ndarray) -> AnomalyScore:
        """Score a single feature vector, shape (n_features,)."""
        if not self.fitted:
            raise RuntimeError("AnomalyDetector.score called before fit()")
        v = np.asarray(features, dtype=float).reshape(1, -1)
        d = float(self._mahalanobis(v)[0])
        return AnomalyScore(is_anomalous=d > self._threshold, score=d)

    def _mahalanobis(self, X: np.ndarray) -> np.ndarray:
        assert self._mean is not None and self._inv_cov is not None
        delta = X - self._mean
        # sqrt of the quadratic form delta @ inv_cov @ delta.T, per row
        return np.sqrt(np.einsum("ij,jk,ik->i", delta, self._inv_cov, delta))
