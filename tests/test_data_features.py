"""Tests for batch feature extraction.

The load-bearing test here is `test_batch_matches_scalar_definitions`: it binds
`reborn.data.features` to `reborn.sensing.features` so the fast path cannot drift
away from the definitions the runtime uses.
"""

from __future__ import annotations

import numpy as np
import pytest

from reborn.data.features import FEATURE_NAMES, batch_features, feature_matrix, standardize
from reborn.data.loaders import SyntheticDriftLoader
from reborn.data.pipeline import PreprocessConfig, build_window_set
from reborn.sensing.features import extract_features, slope_sign_changes, waveform_length

PERMISSIVE_QC = {"min_rms": 0.0, "max_rms": 1e9, "max_offset": 1e9, "saturation_limit": 1e9}


@pytest.fixture
def windows():
    rng = np.random.default_rng(0)
    return rng.standard_normal((25, 200, 3))


def test_batch_matches_scalar_definitions(windows):
    """One source of truth for what a feature is."""
    matrix, names = batch_features(windows)

    for w in range(windows.shape[0]):
        for c in range(windows.shape[2]):
            scalar = extract_features(windows[w, :, c])
            for feature in FEATURE_NAMES:
                column = names.index(f"{feature}_ch{c}")
                assert matrix[w, column] == pytest.approx(scalar[feature]), (
                    f"{feature} ch{c} window {w}"
                )


def test_column_names_and_shape(windows):
    matrix, names = batch_features(windows)

    assert matrix.shape == (25, 3 * len(FEATURE_NAMES))
    assert len(names) == matrix.shape[1]
    assert names[0] == "rms_ch0"
    assert "ssc_ch2" in names


def test_feature_subset_is_respected(windows):
    matrix, names = batch_features(windows, features=("rms", "wl"))

    assert matrix.shape == (25, 3 * 2)
    assert all(n.startswith(("rms_", "wl_")) for n in names)


def test_unknown_feature_is_rejected(windows):
    with pytest.raises(ValueError, match="unknown features"):
        batch_features(windows, features=("rms", "entropy"))


def test_two_dimensional_input_is_rejected():
    with pytest.raises(ValueError, match=r"n_windows, samples, channels"):
        batch_features(np.zeros((10, 200)))


def test_feature_matrix_runs_on_a_window_set():
    loader = SyntheticDriftLoader(n_subjects=1, n_sessions=1, n_blocks=2, block_seconds=0.5)
    window_set = build_window_set(loader.load(), PreprocessConfig(qc_kwargs=PERMISSIVE_QC))

    matrix, names = feature_matrix(window_set)

    assert matrix.shape == (window_set.n_windows, window_set.n_channels * len(FEATURE_NAMES))
    assert np.isfinite(matrix).all()
    assert len(names) == matrix.shape[1]


# --------------------------------------------------------------------------- #
# The new Hudgins features
# --------------------------------------------------------------------------- #


def test_waveform_length_grows_with_amplitude():
    x = np.sin(np.linspace(0, 8 * np.pi, 200))
    assert waveform_length(2 * x) == pytest.approx(2 * waveform_length(x))


def test_waveform_length_of_a_constant_window_is_zero():
    assert waveform_length(np.full(100, 0.3)) == 0.0


def test_slope_sign_changes_counts_reversals():
    # A sawtooth reverses once per period; a monotone ramp never does.
    assert slope_sign_changes(np.arange(100, dtype=float)) == 0.0
    alternating = np.tile([0.0, 1.0], 50)
    assert slope_sign_changes(alternating) > 0.9


def test_short_windows_degrade_to_zero_rather_than_raising():
    assert waveform_length(np.array([1.0])) == 0.0
    assert slope_sign_changes(np.array([1.0, 2.0])) == 0.0

    matrix, _ = batch_features(np.zeros((2, 2, 1)))
    assert np.isfinite(matrix).all()


# --------------------------------------------------------------------------- #
# Standardisation
# --------------------------------------------------------------------------- #


def test_standardize_uses_training_statistics_only():
    """Fitting the scaler on test data leaks the drift being measured."""
    train = np.array([[0.0, 10.0], [2.0, 20.0]])
    test = np.array([[4.0, 30.0]])

    scaled_train, scaled_test = standardize(train, test)

    assert scaled_train.mean(axis=0) == pytest.approx([0.0, 0.0])
    # The test row keeps its offset from the training distribution rather than
    # being recentred onto it.
    assert scaled_test[0, 0] > scaled_train.max()


def test_standardize_survives_a_constant_feature():
    train = np.array([[1.0, 5.0], [1.0, 7.0]])

    (scaled,) = standardize(train)

    assert np.isfinite(scaled).all()
    assert np.all(scaled[:, 0] == 0.0)
