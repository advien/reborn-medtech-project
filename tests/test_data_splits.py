"""Tests for the phase-B evaluation protocols.

The whole value of these protocols is that they do not leak. Each test below
asserts a specific leak is impossible, because a leak here does not raise — it
produces a plausible-looking number that is simply wrong.
"""

from __future__ import annotations

import numpy as np
import pytest

from reborn.data import PreprocessConfig, build_window_set
from reborn.data.loaders import SyntheticDriftLoader
from reborn.data.splits import (
    add_calibration_repetitions,
    Split,
    add_calibration,
    cross_session_splits,
    cross_subject_splits,
    default_guard,
    random_window_split,
    within_session_splits,
)

PERMISSIVE_QC = {"min_rms": 0.0, "max_rms": 1e9, "max_offset": 1e9, "saturation_limit": 1e9}


@pytest.fixture
def window_set():
    loader = SyntheticDriftLoader(n_subjects=3, n_sessions=4, n_blocks=3, block_seconds=0.5)
    return build_window_set(loader.load(), PreprocessConfig(qc_kwargs=PERMISSIVE_QC))


def test_split_rejects_overlapping_indices():
    with pytest.raises(ValueError, match="both train and test"):
        Split(name="bad", train_index=np.array([1, 2, 3]), test_index=np.array([3, 4]))


# --------------------------------------------------------------------------- #
# Cross-session — the core protocol
# --------------------------------------------------------------------------- #


def test_cross_session_never_puts_a_session_on_both_sides(window_set):
    splits = cross_session_splits(window_set, n_train_sessions=1)
    assert splits

    for split in splits:
        train_sessions = set(window_set.session_ids[split.train_index].astype(str))
        test_sessions = set(window_set.session_ids[split.test_index].astype(str))
        assert train_sessions.isdisjoint(test_sessions)


def test_cross_session_keeps_the_subject_fixed(window_set):
    for split in cross_session_splits(window_set, n_train_sessions=2):
        subjects = set(window_set.subject_ids[split.train_index].astype(str))
        subjects |= set(window_set.subject_ids[split.test_index].astype(str))
        assert subjects == {split.meta["subject"]}


def test_cross_session_reports_how_many_sessions_elapsed(window_set):
    """Degradation versus elapsed sessions is the result; averaging hides it."""
    splits = cross_session_splits(window_set, n_train_sessions=1)
    elapsed = sorted({s.meta["sessions_elapsed"] for s in splits})
    assert elapsed == [1, 2, 3]


def test_cross_session_yields_nothing_when_there_is_only_one_session():
    loader = SyntheticDriftLoader(n_subjects=2, n_sessions=1, n_blocks=2, block_seconds=0.5)
    single = build_window_set(loader.load(), PreprocessConfig(qc_kwargs=PERMISSIVE_QC))

    assert cross_session_splits(single, n_train_sessions=1) == []


# --------------------------------------------------------------------------- #
# Cross-subject
# --------------------------------------------------------------------------- #


def test_cross_subject_is_leave_one_subject_out(window_set):
    splits = cross_subject_splits(window_set)
    assert len(splits) == 3

    for split in splits:
        held_out = split.meta["held_out_subject"]
        assert set(window_set.subject_ids[split.test_index].astype(str)) == {held_out}
        assert held_out not in set(window_set.subject_ids[split.train_index].astype(str))


# --------------------------------------------------------------------------- #
# Within-session — temporal, with a guard band
# --------------------------------------------------------------------------- #


def test_within_session_stays_inside_one_session(window_set):
    for split in within_session_splits(window_set):
        sessions = set(window_set.session_ids[split.train_index].astype(str))
        sessions |= set(window_set.session_ids[split.test_index].astype(str))
        assert sessions == {split.meta["session"]}


def test_within_session_leaves_a_guard_band_of_overlapping_windows(window_set):
    guard = default_guard(window_set)
    assert guard > 0, "200 ms / 50 ms windows overlap; the guard must be non-zero"

    for split in within_session_splits(window_set):
        # No training window may sit within `guard` positions of the first test
        # window, or the two share samples.
        assert split.train_index.max() + guard <= split.test_index.min()


def test_default_guard_is_zero_when_stride_is_unknown(window_set):
    stripped = type(window_set)(
        windows=window_set.windows,
        labels=window_set.labels,
        subject_ids=window_set.subject_ids,
        session_ids=window_set.session_ids,
        sample_rate=window_set.sample_rate,
        qc=window_set.qc,
    )
    assert default_guard(stripped) == 0


# --------------------------------------------------------------------------- #
# The control condition
# --------------------------------------------------------------------------- #


def test_random_split_is_disjoint_and_flags_itself_as_leaky(window_set):
    split = random_window_split(window_set, test_fraction=0.3, seed=0)

    assert np.intersect1d(split.train_index, split.test_index).size == 0
    assert split.train_index.size + split.test_index.size == window_set.n_windows
    assert "leaky" in split.meta["warning"]


# --------------------------------------------------------------------------- #
# Few-shot calibration
# --------------------------------------------------------------------------- #


def test_calibration_windows_leave_the_test_set(window_set):
    base = cross_session_splits(window_set, n_train_sessions=1)[0]

    calibrated = add_calibration(base, window_set, n_per_class=3)

    assert np.intersect1d(calibrated.train_index, calibrated.test_index).size == 0
    assert calibrated.train_index.size > base.train_index.size
    assert calibrated.test_index.size < base.test_index.size
    # Everything added came from the session under test, nowhere else.
    added = np.setdiff1d(calibrated.train_index, base.train_index)
    assert np.isin(added, base.test_index).all()


def test_calibration_takes_windows_from_every_class(window_set):
    base = cross_session_splits(window_set, n_train_sessions=1)[0]
    calibrated = add_calibration(base, window_set, n_per_class=2)

    added = np.setdiff1d(calibrated.train_index, base.train_index)
    classes = set(window_set.labels[added].tolist())

    assert classes == set(window_set.labels[base.test_index].tolist())


def test_calibration_that_would_consume_the_test_set_raises(window_set):
    base = cross_session_splits(window_set, n_train_sessions=1)[0]
    with pytest.raises(ValueError, match="consumed the entire test set"):
        add_calibration(base, window_set, n_per_class=base.test_index.size)


# --------------------------------------------------------------------------- #
# Repetition-aware splitting — block-designed datasets
# --------------------------------------------------------------------------- #


def _blocked_window_set():
    """A window set shaped like Ninapro: each class in its own contiguous block.

    This is the structure that breaks a temporal within-session split, so the
    fixture reproduces it rather than the interleaved layout the synthetic
    loader produces.
    """
    from reborn.data.records import QcReport, WindowSet

    n_classes, n_reps, per_rep = 4, 5, 6
    windows, labels, reps = [], [], []
    rng = np.random.default_rng(0)
    for label in range(1, n_classes + 1):          # classes 1..4, in blocks
        for repetition in range(1, n_reps + 1):
            for _ in range(per_rep):
                windows.append(rng.standard_normal((20, 1)))
                labels.append(label)
                reps.append(repetition)
            for _ in range(2):                      # rest between repetitions
                windows.append(0.01 * rng.standard_normal((20, 1)))
                labels.append(0)
                reps.append(0)
    n = len(windows)
    return WindowSet(
        windows=np.stack(windows),
        labels=np.asarray(labels),
        subject_ids=np.asarray(["s01"] * n, dtype=object),
        session_ids=np.asarray(["d01"] * n, dtype=object),
        sample_rate=1000.0,
        qc=QcReport(total=n, kept=n),
        repetition_ids=np.asarray(reps),
    )


def test_temporal_split_would_lose_whole_classes_on_blocked_data():
    """The flaw this protocol change exists to fix, pinned as a test."""
    blocked = _blocked_window_set()
    cut = int(blocked.n_windows * 0.7)

    train_classes = set(blocked.labels[:cut].tolist())
    test_classes = set(blocked.labels[cut:].tolist())

    assert test_classes - train_classes, "expected unseen classes in a naive temporal cut"


def test_repetition_split_keeps_every_class_on_both_sides():
    blocked = _blocked_window_set()

    splits = within_session_splits(blocked)

    assert len(splits) == 1
    split = splits[0]
    train_classes = set(blocked.labels[split.train_index].tolist())
    test_classes = set(blocked.labels[split.test_index].tolist())
    assert train_classes == test_classes


def test_repetition_split_never_shares_a_repetition():
    blocked = _blocked_window_set()
    split = within_session_splits(blocked)[0]
    reps = np.asarray(blocked.repetition_ids)

    train_reps = set(reps[split.train_index].tolist()) - {0}
    test_reps = set(reps[split.test_index].tolist()) - {0}

    assert train_reps.isdisjoint(test_reps)
    assert split.meta["split_by"] == "repetition"


def test_temporal_fallback_flags_itself(window_set):
    """Without repetition numbers the protocol degrades, and says so."""
    assert window_set.repetition_ids is None

    split = within_session_splits(window_set)[0]

    assert split.meta["split_by"] == "time"
    assert "blocked" in split.meta["warning"]


def test_calibration_by_repetition_moves_whole_repetitions():
    blocked = _blocked_window_set()
    base = within_session_splits(blocked)[0]
    reps = np.asarray(blocked.repetition_ids)

    calibrated = add_calibration_repetitions(base, blocked, n_repetitions=1)

    moved = np.setdiff1d(calibrated.train_index, base.train_index)
    moved_reps = set(reps[moved].tolist())
    assert len(moved_reps) == 1
    # Nothing from that repetition is left behind on the test side.
    assert not set(reps[calibrated.test_index].tolist()) & moved_reps
    assert np.intersect1d(calibrated.train_index, calibrated.test_index).size == 0


def test_calibration_by_repetition_needs_repetition_numbers(window_set):
    base = within_session_splits(window_set)[0]
    with pytest.raises(ValueError, match="no repetition numbers"):
        add_calibration_repetitions(base, window_set, n_repetitions=1)


def test_calibration_cannot_consume_every_test_repetition():
    blocked = _blocked_window_set()
    base = within_session_splits(blocked)[0]
    with pytest.raises(ValueError, match="leaves nothing to test on"):
        add_calibration_repetitions(base, blocked, n_repetitions=99)
