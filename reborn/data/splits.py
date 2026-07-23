"""Evaluation protocols for phase B.

Four protocols, each isolating one factor (`docs/research/phase-b-plan.md` §6):

| Protocol | Measures |
|---|---|
| `within_session_splits` | Ceiling |
| `cross_session_splits`  | Drift — the core result |
| `cross_subject_splits`  | Worst case, no calibration |
| `random_window_split`   | The naive protocol, reported once to show its inflation |

Two leakage traps this module exists to close:

1. **Overlapping windows.** At 200 ms / 50 ms, each window shares three quarters
   of its samples with its neighbour. A random split therefore puts near-copies
   of the same window on both sides of the train/test line. Every temporal split
   here leaves a guard band of overlapping windows unassigned.
2. **Session identity.** Cross-session performance is the whole question, so a
   session must never appear on both sides. The protocols group on
   `WindowSet.session_ids` rather than trusting an ordering.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .records import WindowSet


@dataclass(frozen=True)
class Split:
    """One train/test partition, as index arrays into a `WindowSet`."""

    name: str
    train_index: np.ndarray
    test_index: np.ndarray
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        overlap = np.intersect1d(self.train_index, self.test_index)
        if overlap.size:
            raise ValueError(f"split {self.name!r} has {overlap.size} windows in both train and test")

    def apply(self, window_set: WindowSet) -> tuple[WindowSet, WindowSet]:
        return window_set.subset(self.train_index), window_set.subset(self.test_index)


def default_guard(window_set: WindowSet) -> int:
    """Windows to leave unassigned at a temporal boundary so none overlap across it.

    Derived from the window/stride ratio recorded by
    `reborn.data.pipeline.build_window_set`; falls back to 0 when unknown, which
    is only correct for non-overlapping windows.
    """
    width = window_set.meta.get("window_samples")
    stride = window_set.meta.get("stride_samples")
    if not width or not stride:
        return 0
    return max(0, math.ceil(float(width) / float(stride)) - 1)


# --------------------------------------------------------------------------- #
# Protocols
# --------------------------------------------------------------------------- #


def within_session_splits(
    window_set: WindowSet, train_fraction: float = 0.7, guard: int | None = None
) -> list[Split]:
    """Ceiling: train and test inside one session.

    **Splits by repetition when the dataset provides repetition numbers**, and
    falls back to a temporal cut otherwise.

    The distinction is not cosmetic. Block-designed datasets — Ninapro among them
    — record every repetition of one gesture, then every repetition of the next.
    A contiguous temporal cut through such a recording puts whole classes on one
    side of the line: on DB6 a 70/30 cut trains on classes {0,1,3,4,6,9} and
    tests on {0,9,10,11}, so two classes are never trained and four never tested.
    The resulting "ceiling" sits *below* the cross-session score, which is how
    the flaw announces itself.

    Repetition-wise splitting is also the Ninapro convention, so the numbers stay
    comparable to the literature. Held-out repetitions are the later ones, which
    keeps the split temporal *within* each gesture block.
    """
    if window_set.repetition_ids is not None:
        return _within_session_by_repetition(window_set, train_fraction)

    guard = default_guard(window_set) if guard is None else guard
    splits: list[Split] = []
    for subject, session, index in _groups(window_set):
        cut = int(len(index) * train_fraction)
        train = index[: max(0, cut - guard)]
        test = index[cut:]
        if train.size == 0 or test.size == 0:
            continue
        splits.append(
            Split(
                name=f"within/{subject}/{session}",
                train_index=train,
                test_index=test,
                meta={
                    "subject": subject,
                    "session": session,
                    "guard": guard,
                    "split_by": "time",
                    # Loud on purpose: if the dataset is block-designed, this
                    # number is not a ceiling and should not be reported as one.
                    "warning": "temporal cut — verify classes are interleaved, not blocked",
                },
            )
        )
    return splits


def _within_session_by_repetition(window_set: WindowSet, train_fraction: float) -> list[Split]:
    """Hold out the later repetitions of every gesture."""
    repetitions = np.asarray(window_set.repetition_ids)
    splits: list[Split] = []

    for subject, session, index in _groups(window_set):
        # Repetition 0 marks rest/between-repetition samples in Ninapro; it spans
        # the whole session and belongs on both sides in proportion, so it is
        # assigned by its own ordering rather than held out wholesale.
        session_reps = repetitions[index]
        numbered = np.unique(session_reps[session_reps > 0])
        if numbered.size < 2:
            continue

        cut = max(1, int(len(numbered) * train_fraction))
        train_reps, test_reps = numbered[:cut], numbered[cut:]
        if test_reps.size == 0:
            continue

        train_mask = np.isin(session_reps, train_reps)
        test_mask = np.isin(session_reps, test_reps)

        # Split the rest windows in the same proportion, temporally, so the class
        # balance of both sides resembles the session's.
        rest_positions = np.flatnonzero(session_reps == 0)
        rest_cut = int(rest_positions.size * train_fraction)
        train_mask[rest_positions[:rest_cut]] = True
        test_mask[rest_positions[rest_cut:]] = True

        train, test = index[train_mask], index[test_mask]
        if train.size == 0 or test.size == 0:
            continue
        splits.append(
            Split(
                name=f"within/{subject}/{session}",
                train_index=train,
                test_index=test,
                meta={
                    "subject": subject,
                    "session": session,
                    "split_by": "repetition",
                    "train_repetitions": train_reps.tolist(),
                    "test_repetitions": test_reps.tolist(),
                },
            )
        )
    return splits


def cross_session_splits(window_set: WindowSet, n_train_sessions: int = 1) -> list[Split]:
    """Drift: train on a subject's earliest sessions, test on each later one.

    Sessions are ordered by their identifier, so backends must emit session ids
    that sort chronologically (zero-padded, e.g. `d01_s2`). One split per
    (subject, held-out session) keeps degradation-versus-elapsed-sessions
    visible instead of averaging it away.
    """
    splits: list[Split] = []
    for subject, sessions in _sessions_by_subject(window_set).items():
        if len(sessions) <= n_train_sessions:
            continue
        train_sessions = sessions[:n_train_sessions]
        train = _index_for_sessions(window_set, subject, train_sessions)
        for offset, session in enumerate(sessions[n_train_sessions:], start=1):
            test = _index_for_sessions(window_set, subject, [session])
            if train.size == 0 or test.size == 0:
                continue
            splits.append(
                Split(
                    name=f"cross-session/{subject}/{session}",
                    train_index=train,
                    test_index=test,
                    meta={
                        "subject": subject,
                        "train_sessions": train_sessions,
                        "test_session": session,
                        "sessions_elapsed": offset,
                    },
                )
            )
    return splits


def cross_subject_splits(window_set: WindowSet) -> list[Split]:
    """Worst case: leave-one-subject-out, no calibration on the held-out subject."""
    subjects = sorted({str(s) for s in window_set.subject_ids})
    splits: list[Split] = []
    for held_out in subjects:
        mask = window_set.subject_ids.astype(str) == held_out
        test = np.flatnonzero(mask)
        train = np.flatnonzero(~mask)
        if train.size == 0 or test.size == 0:
            continue
        splits.append(
            Split(
                name=f"cross-subject/{held_out}",
                train_index=train,
                test_index=test,
                meta={"held_out_subject": held_out},
            )
        )
    return splits


def random_window_split(
    window_set: WindowSet, test_fraction: float = 0.3, seed: int = 0
) -> Split:
    """The naive protocol — **reported once, as a control**.

    Shuffling at window level puts overlapping near-copies on both sides. The
    resulting number is not a performance estimate; it is a measurement of how
    much the naive protocol inflates, and the paper should present it as such.
    """
    rng = np.random.default_rng(seed)
    order = rng.permutation(window_set.n_windows)
    cut = int(window_set.n_windows * (1.0 - test_fraction))
    return Split(
        name="random-shuffle/control",
        train_index=np.sort(order[:cut]),
        test_index=np.sort(order[cut:]),
        meta={"warning": "leaky by construction — control condition only", "seed": seed},
    )


# --------------------------------------------------------------------------- #
# Few-shot personalization
# --------------------------------------------------------------------------- #


def add_calibration_repetitions(
    split: Split, window_set: WindowSet, n_repetitions: int
) -> Split:
    """Move the first `n_repetitions` of the test session into training.

    This is the few-shot arm as `docs/research/phase-b-plan.md` §6 specifies it:
    calibration is measured in **repetitions**, because that is the unit a user
    actually performs at the start of a session. Counting windows instead would
    quote a calibration cost that means nothing to anyone wearing the device —
    and, since windows overlap, would let fragments of one repetition sit on both
    sides of the line.

    Rest windows are not moved: rest is not something a user is asked to repeat.
    """
    if window_set.repetition_ids is None:
        raise ValueError(
            "this window set has no repetition numbers — use add_calibration (per-window) "
            "or load a dataset whose loader provides them"
        )
    repetitions = np.asarray(window_set.repetition_ids)
    test_reps = repetitions[split.test_index]
    numbered = np.unique(test_reps[test_reps > 0])
    if numbered.size <= n_repetitions:
        raise ValueError(
            f"calibration of {n_repetitions} repetitions leaves nothing to test on for "
            f"{split.name} ({numbered.size} available)"
        )

    chosen = numbered[:n_repetitions]
    calibration = split.test_index[np.isin(test_reps, chosen)]
    remaining = np.setdiff1d(split.test_index, calibration)

    return Split(
        name=f"{split.name}+cal{n_repetitions}rep",
        train_index=np.sort(np.concatenate([split.train_index, calibration])),
        test_index=remaining,
        meta={
            **split.meta,
            "calibration_repetitions": chosen.tolist(),
            "calibration_windows": int(calibration.size),
        },
    )


def add_calibration(
    split: Split,
    window_set: WindowSet,
    n_per_class: int,
    seed: int = 0,
) -> Split:
    """Move `n_per_class` windows per class from the test side into training.

    The per-window variant, for datasets without repetition numbers. Prefer
    `add_calibration_repetitions` where they exist: repetitions are the unit a
    user actually performs, and windows overlap, so a window budget can split one
    repetition across the train/test line.

    Calibration windows are taken from the **earliest** part of the test session,
    matching how a real session starts with a short calibration and is then used.
    """
    rng = np.random.default_rng(seed)
    labels = window_set.labels[split.test_index]
    calibration: list[int] = []
    for label in np.unique(labels):
        candidates = split.test_index[labels == label]
        take = min(n_per_class, candidates.size)
        calibration.extend(candidates[:take].tolist())
    calibration_array = np.asarray(sorted(calibration), dtype=int)
    remaining = np.setdiff1d(split.test_index, calibration_array)
    if remaining.size == 0:
        raise ValueError(
            f"calibration of {n_per_class} per class consumed the entire test set for {split.name}"
        )
    rng.shuffle(calibration_array)  # order-independence of the calibration set
    return Split(
        name=f"{split.name}+cal{n_per_class}",
        train_index=np.sort(np.concatenate([split.train_index, calibration_array])),
        test_index=remaining,
        meta={**split.meta, "calibration_per_class": n_per_class, "seed": seed},
    )


# --------------------------------------------------------------------------- #
# Internals
# --------------------------------------------------------------------------- #


def _groups(window_set: WindowSet) -> list[tuple[str, str, np.ndarray]]:
    """`(subject, session, window indices)`, indices in original (temporal) order."""
    subjects = window_set.subject_ids.astype(str)
    sessions = window_set.session_ids.astype(str)
    seen: dict[tuple[str, str], list[int]] = {}
    for i, (subject, session) in enumerate(zip(subjects, sessions)):
        seen.setdefault((subject, session), []).append(i)
    return [
        (subject, session, np.asarray(index, dtype=int))
        for (subject, session), index in sorted(seen.items())
    ]


def _sessions_by_subject(window_set: WindowSet) -> dict[str, list[str]]:
    subjects = window_set.subject_ids.astype(str)
    sessions = window_set.session_ids.astype(str)
    out: dict[str, set[str]] = {}
    for subject, session in zip(subjects, sessions):
        out.setdefault(subject, set()).add(session)
    return {subject: sorted(values) for subject, values in sorted(out.items())}


def _index_for_sessions(window_set: WindowSet, subject: str, sessions: list[str]) -> np.ndarray:
    mask = (window_set.subject_ids.astype(str) == subject) & np.isin(
        window_set.session_ids.astype(str), sessions
    )
    return np.flatnonzero(mask)
