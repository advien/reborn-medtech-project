"""Tests for the phase-B data layer.

These cover the two things that would silently corrupt every phase-B number if
they were wrong — window causality and QC rejection accounting — plus the record
invariants the split protocols rely on.
"""

from __future__ import annotations

import numpy as np
import pytest

from reborn.data import EmgRecording, PreprocessConfig, build_window_set
from reborn.data.loaders import SyntheticDriftLoader
from reborn.data.pipeline import (
    load_window_set,
    resample_recording,
    save_window_set,
    window_recording,
)

# Thresholds in reborn.sensing.emg_qc are absolute and therefore scale-dependent;
# these switch the amplitude checks off so a test asserting *windowing* behaviour
# is not also asserting that arbitrary test amplitudes pass QC.
PERMISSIVE_QC = {
    "min_rms": 0.0,
    "max_rms": 1e9,
    "max_offset": 1e9,
    "saturation_limit": 1e9,
}


def _recording(signal: np.ndarray, labels: np.ndarray, sample_rate: float = 1000.0, **kwargs):
    return EmgRecording(
        signal=signal,
        sample_rate=sample_rate,
        labels=labels,
        subject_id=kwargs.pop("subject_id", "s01"),
        session_id=kwargs.pop("session_id", "d01"),
        **kwargs,
    )


# --------------------------------------------------------------------------- #
# Records
# --------------------------------------------------------------------------- #


def test_one_dimensional_signal_becomes_single_channel():
    rec = _recording(np.zeros(100), np.zeros(100, dtype=int))
    assert rec.signal.shape == (100, 1)
    assert rec.n_channels == 1


def test_label_length_must_match_sample_count():
    with pytest.raises(ValueError, match="one entry per sample"):
        _recording(np.zeros((100, 2)), np.zeros(50, dtype=int))


def test_session_id_is_required():
    with pytest.raises(ValueError, match="subject_id and session_id"):
        EmgRecording(
            signal=np.zeros((10, 1)),
            sample_rate=1000.0,
            labels=np.zeros(10, dtype=int),
            subject_id="s01",
            session_id="",
        )


# --------------------------------------------------------------------------- #
# Resampling
# --------------------------------------------------------------------------- #


def test_resampling_halves_length_and_keeps_labels_categorical():
    labels = np.repeat([0, 3, 0, 5], 500)
    rec = _recording(np.random.default_rng(0).standard_normal((2000, 2)), labels, sample_rate=2000.0)

    out = resample_recording(rec, 1000.0)

    assert out.sample_rate == 1000.0
    assert out.n_samples == pytest.approx(1000, abs=2)
    assert out.labels.shape[0] == out.n_samples
    # Labels are class ids: resampling must never interpolate them into new values.
    assert set(np.unique(out.labels)).issubset({0, 3, 5})


def test_resampling_is_a_no_op_at_the_target_rate():
    rec = _recording(np.zeros((100, 1)), np.zeros(100, dtype=int))
    assert resample_recording(rec, 1000.0) is rec


# --------------------------------------------------------------------------- #
# Windowing — causality is the load-bearing property
# --------------------------------------------------------------------------- #


def test_window_is_labelled_by_its_last_sample():
    # Label flips at sample 500. A window ending at or after 500 is class 1;
    # anything else means the window is reading its label from the future.
    labels = np.concatenate([np.zeros(500, dtype=int), np.ones(500, dtype=int)])
    rec = _recording(np.random.default_rng(0).standard_normal((1000, 1)), labels)
    config = PreprocessConfig(
        window_ms=100.0, stride_ms=50.0, pure_windows=False, qc_kwargs=PERMISSIVE_QC
    )

    windows, window_labels, _ = window_recording(rec, config)

    width = config.window_samples
    starts = np.arange(0, 1000 - width + 1, config.stride_samples)
    expected = labels[starts + width - 1]
    assert windows.shape[0] == starts.size
    np.testing.assert_array_equal(window_labels, expected)


def test_pure_windows_drops_transition_windows():
    labels = np.concatenate([np.zeros(500, dtype=int), np.ones(500, dtype=int)])
    rec = _recording(np.random.default_rng(0).standard_normal((1000, 1)), labels)
    mixed = PreprocessConfig(window_ms=100.0, stride_ms=50.0, pure_windows=False, qc_kwargs=PERMISSIVE_QC)
    pure = PreprocessConfig(window_ms=100.0, stride_ms=50.0, pure_windows=True, qc_kwargs=PERMISSIVE_QC)

    _, mixed_labels, _ = window_recording(rec, mixed)
    _, pure_labels, _ = window_recording(rec, pure)

    assert pure_labels.size < mixed_labels.size


def test_recording_shorter_than_one_window_yields_nothing():
    rec = _recording(np.zeros((50, 1)), np.zeros(50, dtype=int))
    config = PreprocessConfig(window_ms=200.0, qc_kwargs=PERMISSIVE_QC)

    windows, labels, qc = window_recording(rec, config)

    assert windows.shape[0] == 0
    assert labels.size == 0
    assert qc.total == 0


# --------------------------------------------------------------------------- #
# QC gate — the rejection rate is a reported result, so it must add up
# --------------------------------------------------------------------------- #


def test_qc_rejects_a_flatlined_channel_and_accounts_for_it():
    rng = np.random.default_rng(0)
    signal = 0.05 * rng.standard_normal((1000, 2))
    signal[400:700, 1] = 0.0  # lead-off on channel 1 for 300 ms
    rec = _recording(signal, np.ones(1000, dtype=int))
    config = PreprocessConfig(window_ms=100.0, stride_ms=100.0, qc_kwargs=PERMISSIVE_QC)

    _, _, qc = window_recording(rec, config)

    assert qc.rejected > 0
    assert "dropout" in qc.rejected_by_reason
    assert qc.kept + qc.rejected == qc.total
    assert 0.0 < qc.rejection_rate < 1.0


def test_clean_signal_passes_the_gate_intact():
    rng = np.random.default_rng(0)
    rec = _recording(0.05 * rng.standard_normal((1000, 2)), np.ones(1000, dtype=int))
    config = PreprocessConfig(window_ms=100.0, stride_ms=100.0, qc_kwargs=PERMISSIVE_QC)

    _, _, qc = window_recording(rec, config)

    assert qc.rejected == 0
    assert qc.rejection_rate == 0.0


def test_qc_channels_restricts_which_channels_are_inspected():
    rng = np.random.default_rng(0)
    signal = 0.05 * rng.standard_normal((1000, 2))
    signal[:, 1] = 0.0  # channel 1 entirely dead
    rec = _recording(signal, np.ones(1000, dtype=int))
    common = dict(window_ms=100.0, stride_ms=100.0, qc_kwargs=PERMISSIVE_QC)

    _, _, all_channels = window_recording(rec, PreprocessConfig(**common))
    _, _, channel_zero = window_recording(rec, PreprocessConfig(qc_channels=(0,), **common))

    assert all_channels.rejected == all_channels.total
    assert channel_zero.rejected == 0


def test_out_of_range_qc_channel_is_rejected_loudly():
    rec = _recording(np.zeros((1000, 2)), np.zeros(1000, dtype=int))
    config = PreprocessConfig(qc_channels=(5,))
    with pytest.raises(ValueError, match="out of range"):
        window_recording(rec, config)


# --------------------------------------------------------------------------- #
# WindowSet assembly and cache
# --------------------------------------------------------------------------- #


def test_build_window_set_keeps_provenance_per_window():
    loader = SyntheticDriftLoader(n_subjects=2, n_sessions=2, n_blocks=2, block_seconds=0.5)
    config = PreprocessConfig(qc_kwargs=PERMISSIVE_QC)

    window_set = build_window_set(loader.load(), config)

    assert window_set.n_windows > 0
    assert window_set.subject_ids.shape[0] == window_set.n_windows
    assert set(window_set.subject_ids.astype(str)) == {"s01", "s02"}
    assert set(window_set.session_ids.astype(str)) == {"d01", "d02"}
    assert window_set.meta["config_fingerprint"] == config.fingerprint()


def test_binary_labels_collapse_to_rest_versus_active():
    loader = SyntheticDriftLoader(n_subjects=1, n_sessions=1, n_blocks=2, block_seconds=0.5)
    window_set = build_window_set(loader.load(), PreprocessConfig(qc_kwargs=PERMISSIVE_QC))

    binary = window_set.binary_labels()

    assert set(np.unique(binary)) == {0, 1}
    np.testing.assert_array_equal(binary, (window_set.labels != 0).astype(int))


def test_config_fingerprint_changes_with_the_configuration():
    assert PreprocessConfig().fingerprint() != PreprocessConfig(window_ms=150.0).fingerprint()
    assert PreprocessConfig().fingerprint() == PreprocessConfig().fingerprint()


def test_cache_roundtrip_preserves_windows_and_qc_counts(tmp_path):
    loader = SyntheticDriftLoader(n_subjects=1, n_sessions=2, n_blocks=2, block_seconds=0.5)
    config = PreprocessConfig(qc_kwargs=PERMISSIVE_QC)
    original = build_window_set(loader.load(), config)

    path = save_window_set(original, tmp_path / "cache.npz", config)
    restored = load_window_set(path)

    np.testing.assert_allclose(restored.windows, original.windows)
    np.testing.assert_array_equal(restored.labels, original.labels)
    np.testing.assert_array_equal(
        restored.session_ids.astype(str), original.session_ids.astype(str)
    )
    assert restored.qc.total == original.qc.total
    assert restored.qc.kept == original.qc.kept
    assert path.with_suffix(".manifest.json").exists()


def test_empty_result_explains_the_likely_cause():
    rec = _recording(np.zeros((1000, 1)), np.zeros(1000, dtype=int))
    with pytest.raises(ValueError, match="qc_kwargs"):
        build_window_set([rec], PreprocessConfig())


# --------------------------------------------------------------------------- #
# The fixture models drift — the property the protocols depend on
# --------------------------------------------------------------------------- #


def test_synthetic_loader_actually_drifts_across_sessions():
    """Without this, a cross-session test would pass for the wrong reason."""
    loader = SyntheticDriftLoader(n_subjects=1, n_sessions=4, n_blocks=2, block_seconds=0.5)
    recordings = {r.session_id: r for r in loader.load()}

    amplitudes = [float(np.sqrt(np.mean(recordings[s].signal**2))) for s in sorted(recordings)]

    assert amplitudes == sorted(amplitudes)
    assert amplitudes[-1] > 1.5 * amplitudes[0]
