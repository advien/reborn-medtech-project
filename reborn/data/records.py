"""Canonical record types for open EMG datasets.

Every dataset backend in `reborn.data.loaders` returns `EmgRecording`, so the
preprocessing pipeline, the evaluation protocols, and the notebooks are written
once rather than per dataset. See `docs/research/phase-b-plan.md` §3–4.

`EmgRecording` deliberately carries `subject_id` and `session_id` as first-class
fields rather than metadata: the phase-B result is about what changes *across
sessions*, so a record that cannot say which session it came from is unusable,
and the splits in `reborn.data.splits` refuse to guess.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

REST_LABEL = 0
"""Label reserved for rest / no intent across all datasets."""


@dataclass(frozen=True)
class EmgRecording:
    """One continuous EMG recording from one subject in one session.

    Args:
        signal: shape `(n_samples, n_channels)`, float.
        sample_rate: Hz.
        labels: shape `(n_samples,)`, integer class per sample. `REST_LABEL` (0)
            means rest / no intent; dataset backends map their own encoding onto
            this so downstream code never needs a per-dataset special case.
        subject_id: stable identifier within the source dataset.
        session_id: stable identifier for the recording session. For datasets
            with several sessions per day this must distinguish them, otherwise
            the cross-session protocol silently becomes within-session.
        trial_id: optional sub-division within a session.
        source: dataset name, e.g. `"ninapro_db6"`.
        meta: anything dataset-specific worth keeping (original rate, channel
            placement, file path).
    """

    signal: np.ndarray
    sample_rate: float
    labels: np.ndarray
    subject_id: str
    session_id: str
    trial_id: str | None = None
    source: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        signal = np.asarray(self.signal, dtype=float)
        if signal.ndim == 1:
            signal = signal[:, None]
        if signal.ndim != 2:
            raise ValueError(f"signal must be (n_samples, n_channels), got shape {signal.shape}")
        labels = np.asarray(self.labels).reshape(-1)
        if labels.shape[0] != signal.shape[0]:
            raise ValueError(
                f"labels ({labels.shape[0]}) must have one entry per sample ({signal.shape[0]})"
            )
        if self.sample_rate <= 0:
            raise ValueError(f"sample_rate must be positive, got {self.sample_rate}")
        if not self.subject_id or not self.session_id:
            raise ValueError("subject_id and session_id are required (see module docstring)")
        object.__setattr__(self, "signal", signal)
        object.__setattr__(self, "labels", labels)

    @property
    def n_samples(self) -> int:
        return int(self.signal.shape[0])

    @property
    def n_channels(self) -> int:
        return int(self.signal.shape[1])

    @property
    def key(self) -> tuple[str, str, str | None]:
        """Identity used by the split protocols."""
        return (self.subject_id, self.session_id, self.trial_id)

    def with_signal(self, signal: np.ndarray, sample_rate: float, labels: np.ndarray) -> EmgRecording:
        """Copy carrying a new signal — used by resampling/filtering steps."""
        return EmgRecording(
            signal=signal,
            sample_rate=sample_rate,
            labels=labels,
            subject_id=self.subject_id,
            session_id=self.session_id,
            trial_id=self.trial_id,
            source=self.source,
            meta=dict(self.meta),
        )


@dataclass(frozen=True)
class QcReport:
    """How many windows the signal-quality gate kept, and why it dropped the rest.

    The rejection rate is a reported result, not bookkeeping: it is what the
    safety layer would have done at runtime (`docs/research/phase-b-plan.md` §5).
    """

    total: int
    kept: int
    rejected_by_reason: dict[str, int] = field(default_factory=dict)

    @property
    def rejected(self) -> int:
        return self.total - self.kept

    @property
    def rejection_rate(self) -> float:
        return self.rejected / self.total if self.total else 0.0

    def merge(self, other: QcReport) -> QcReport:
        reasons = dict(self.rejected_by_reason)
        for reason, count in other.rejected_by_reason.items():
            reasons[reason] = reasons.get(reason, 0) + count
        return QcReport(
            total=self.total + other.total,
            kept=self.kept + other.kept,
            rejected_by_reason=reasons,
        )


@dataclass(frozen=True)
class WindowSet:
    """Windowed, QC-gated dataset ready for feature extraction.

    `subject_ids` / `session_ids` are per-window and parallel to `windows`; the
    split protocols group on them. Keeping them per-window (rather than a
    per-recording index) means a window can never be separated from its
    provenance by a reordering.
    """

    windows: np.ndarray  # (n_windows, window_samples, n_channels)
    labels: np.ndarray  # (n_windows,)
    subject_ids: np.ndarray  # (n_windows,) str
    session_ids: np.ndarray  # (n_windows,) str
    sample_rate: float
    qc: QcReport
    source: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        n = self.windows.shape[0]
        for name in ("labels", "subject_ids", "session_ids"):
            got = np.asarray(getattr(self, name)).shape[0]
            if got != n:
                raise ValueError(f"{name} has {got} entries, expected {n} (one per window)")
        if self.windows.ndim != 3:
            raise ValueError(
                f"windows must be (n_windows, window_samples, n_channels), got {self.windows.shape}"
            )

    @property
    def n_windows(self) -> int:
        return int(self.windows.shape[0])

    @property
    def window_samples(self) -> int:
        return int(self.windows.shape[1])

    @property
    def n_channels(self) -> int:
        return int(self.windows.shape[2])

    def subset(self, index: np.ndarray) -> WindowSet:
        """Rows selected by `index`. QC counts are not re-derived — they describe
        the full gating pass, and a subset of windows has no rejection rate of
        its own."""
        index = np.asarray(index)
        return WindowSet(
            windows=self.windows[index],
            labels=self.labels[index],
            subject_ids=self.subject_ids[index],
            session_ids=self.session_ids[index],
            sample_rate=self.sample_rate,
            qc=self.qc,
            source=self.source,
            meta=dict(self.meta),
        )

    def binary_labels(self) -> np.ndarray:
        """Rest vs. any non-rest — Reborn's flex / no-flex reduction.

        The multi-class labels stay available so the paper can report both and
        the reduction is visible (`docs/research/phase-b-plan.md` §3).
        """
        return (self.labels != REST_LABEL).astype(int)
