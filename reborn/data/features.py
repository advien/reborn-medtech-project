"""Batch feature extraction over a `WindowSet`.

`reborn.sensing.features` defines what each feature *is*, one window at a time,
and stays the single source of truth. This module computes the same quantities
across a whole `WindowSet` at once, because a phase-B run covers hundreds of
thousands of windows and a Python loop over them dominates the runtime.

The duplication is deliberate but bounded: `tests/test_data_features.py` asserts
the batch path reproduces `extract_features` window by window, so the two cannot
drift apart silently. If you add a feature, add it in `reborn.sensing.features`
first and mirror it here — never the other way round.
"""

from __future__ import annotations

import numpy as np

from .records import WindowSet

FEATURE_NAMES = ("rms", "mav", "zcr", "wl", "ssc")


def batch_features(
    windows: np.ndarray, features: tuple[str, ...] = FEATURE_NAMES, threshold: float = 0.0
) -> tuple[np.ndarray, list[str]]:
    """Features for every window and channel.

    Args:
        windows: `(n_windows, window_samples, n_channels)`.
        features: which of `FEATURE_NAMES` to compute, in order.
        threshold: noise floor for `zcr` and `ssc`, as in the scalar versions.

    Returns:
        `(matrix, names)` where matrix is `(n_windows, n_channels * len(features))`
        and names are `"<feature>_ch<k>"`, matching the column order.
    """
    if windows.ndim != 3:
        raise ValueError(f"expected (n_windows, samples, channels), got {windows.shape}")
    unknown = set(features) - set(FEATURE_NAMES)
    if unknown:
        raise ValueError(f"unknown features {sorted(unknown)}; expected {FEATURE_NAMES}")

    x = np.asarray(windows, dtype=float)
    n_samples = x.shape[1]
    computed: dict[str, np.ndarray] = {}

    if {"zcr", "wl", "ssc"} & set(features):
        slope = np.diff(x, axis=1)

    for name in features:
        if name == "rms":
            computed[name] = np.sqrt(np.mean(np.square(x), axis=1))
        elif name == "mav":
            computed[name] = np.mean(np.abs(x), axis=1)
        elif name == "zcr":
            if n_samples < 2:
                computed[name] = np.zeros((x.shape[0], x.shape[2]))
                continue
            signs = np.sign(x)
            signs[signs == 0] = 1
            crossings = np.diff(signs, axis=1) != 0
            significant = np.abs(slope) > threshold
            computed[name] = np.sum(crossings & significant, axis=1) / (n_samples - 1)
        elif name == "wl":
            computed[name] = (
                np.sum(np.abs(slope), axis=1) if n_samples >= 2 else np.zeros((x.shape[0], x.shape[2]))
            )
        elif name == "ssc":
            if n_samples < 3:
                computed[name] = np.zeros((x.shape[0], x.shape[2]))
                continue
            reversed_sign = (slope[:, :-1] * slope[:, 1:]) < 0
            significant = np.maximum(np.abs(slope[:, :-1]), np.abs(slope[:, 1:])) > threshold
            computed[name] = np.sum(reversed_sign & significant, axis=1) / (n_samples - 2)

    n_channels = x.shape[2]
    columns = [computed[name][:, channel] for name in features for channel in range(n_channels)]
    names = [f"{name}_ch{channel}" for name in features for channel in range(n_channels)]
    return np.column_stack(columns), names


def feature_matrix(
    window_set: WindowSet, features: tuple[str, ...] = FEATURE_NAMES
) -> tuple[np.ndarray, list[str]]:
    """`batch_features` applied to a `WindowSet`."""
    return batch_features(window_set.windows, features)


def standardize(train: np.ndarray, *others: np.ndarray) -> tuple[np.ndarray, ...]:
    """Z-score using **training** statistics only, applied to every array given.

    Fitting the scaler on the full dataset leaks test-set statistics into
    training. Under the cross-session protocol that leak is not incidental: the
    per-session shift in signal amplitude *is* the drift being measured, so
    standardising across sessions removes part of the effect under study and
    flatters the result.

    Feature scales here span orders of magnitude — `wl` is an unnormalised sum,
    `zcr` a fraction — so distance-based models need this.
    """
    mean = train.mean(axis=0)
    scale = train.std(axis=0)
    scale[scale == 0] = 1.0  # a constant feature carries no information; leave it at zero
    return tuple((array - mean) / scale for array in (train, *others))
