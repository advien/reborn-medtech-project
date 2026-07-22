"""Tests for per-dataset QC threshold derivation."""

from __future__ import annotations

import numpy as np
import pytest

from reborn.data.loaders import SyntheticDriftLoader
from reborn.data.pipeline import PreprocessConfig, window_recording
from reborn.data.qc_calibration import (
    calibrate,
    profile_amplitudes,
    suggest_corruption_kwargs,
    suggest_qc_thresholds,
)


@pytest.fixture
def recordings():
    loader = SyntheticDriftLoader(n_subjects=2, n_sessions=2, n_blocks=3, block_seconds=0.5)
    return list(loader.load())


def test_profile_covers_every_channel(recordings):
    profile = profile_amplitudes(recordings)

    assert profile.n_windows > 0
    assert profile.n_channels == 2
    assert profile.rms.size == profile.n_windows * profile.n_channels


def test_suggested_thresholds_bracket_the_observed_signal(recordings):
    profile = profile_amplitudes(recordings)

    thresholds = suggest_qc_thresholds(profile)

    assert thresholds["min_rms"] < profile.rms.min()
    assert thresholds["max_rms"] > profile.rms.max()
    assert thresholds["saturation_limit"] > profile.abs_max.max()


def test_suggested_thresholds_keep_clean_data(recordings):
    """The point of calibration: healthy signal must survive its own gate."""
    thresholds = calibrate(recordings)["suggested_qc_kwargs"]
    config = PreprocessConfig(qc_kwargs=thresholds)

    _, _, qc = window_recording(recordings[0], config)

    assert qc.total > 0
    assert qc.rejection_rate < 0.05


def test_suggested_thresholds_still_catch_a_dead_channel(recordings):
    """A gate that rejects nothing is not calibrated, it is disabled."""
    thresholds = calibrate(recordings)["suggested_qc_kwargs"]
    broken = recordings[0]
    signal = broken.signal.copy()
    signal[:, 0] = 0.0
    broken = broken.with_signal(signal, broken.sample_rate, broken.labels)

    _, _, qc = window_recording(broken, PreprocessConfig(qc_kwargs=thresholds))

    assert qc.rejection_rate == 1.0


def test_flatline_threshold_is_calibrated_too(recordings):
    """It is absolute like the rest; left at its default it rejects whole datasets."""
    thresholds = suggest_qc_thresholds(profile_amplitudes(recordings))

    assert "flatline_std" in thresholds
    assert thresholds["flatline_std"] < profile_amplitudes(recordings).rms.min()


def test_corruption_kwargs_scale_to_the_signal(recordings):
    """Absolute defaults inject faults orders of magnitude above a real signal."""
    profile = profile_amplitudes(recordings)

    kwargs = suggest_corruption_kwargs(profile, severity=3.0)

    assert kwargs["noise_burst"]["amplitude"] == pytest.approx(
        float(np.percentile(profile.rms, 50)) * 3.0
    )
    assert kwargs["clipping"]["limit"] > profile.abs_max.max()
    assert kwargs["dropout"] == {}


def test_calibration_records_how_each_threshold_was_derived(recordings):
    result = calibrate(recordings, margin=4.0)

    assert set(result["derivation"]) == set(result["suggested_qc_kwargs"])
    assert "4.0" in result["derivation"]["max_rms"]


def test_larger_margin_widens_the_gate(recordings):
    narrow = calibrate(recordings, margin=2.0)["suggested_qc_kwargs"]
    wide = calibrate(recordings, margin=10.0)["suggested_qc_kwargs"]

    assert wide["max_rms"] > narrow["max_rms"]
    assert wide["saturation_limit"] > narrow["saturation_limit"]


def test_window_sampling_is_capped(recordings):
    capped = profile_amplitudes(recordings, max_windows_per_recording=5)
    assert capped.n_windows == 5 * len(recordings)


def test_recordings_shorter_than_a_window_are_reported(recordings):
    short = recordings[0]
    short = short.with_signal(short.signal[:50], short.sample_rate, short.labels[:50])
    with pytest.raises(ValueError, match="shorter than one window"):
        profile_amplitudes([short])


def test_profile_percentiles_are_ordered(recordings):
    summary = profile_amplitudes(recordings).summary()
    rms = summary["rms"]
    assert rms["p0.1"] <= rms["p50"] <= rms["p99.9"]
    assert np.isfinite(list(rms.values())).all()
