"""Synthetic multi-session EMG — a **fixture, not a dataset**.

Nothing produced from this loader is a result about EMG, and no number derived
from it belongs in a paper. It exists so the pipeline, the split protocols, and
the metric code can be built and tested before tens of gigabytes are downloaded,
and so the test suite runs without any local data — the same role the smoke
fixture plays in `notebooks/01_emg_qc_and_baselines.ipynb`, and labelled the same
way. The roadmap's *real data, not synthetic* principle applies to results, not
to plumbing tests.

What it does model, deliberately, is the one structure the protocols depend on:
a per-session gain and baseline shift, so a cross-session split is actually
harder than a within-session one and a test can assert that.
"""

from __future__ import annotations

from typing import Iterator, Sequence

import numpy as np

from ..records import EmgRecording
from .base import DatasetLoader


class SyntheticDriftLoader(DatasetLoader):
    """Generates rest/active blocks whose statistics drift across sessions.

    Args:
        n_subjects: subjects to generate.
        n_sessions: sessions per subject; session ids sort chronologically.
        n_channels: EMG channels.
        sample_rate: Hz.
        block_seconds: duration of each rest or active block.
        n_blocks: rest/active block pairs per recording.
        drift_per_session: fractional gain change applied per session index — the
            knob that makes cross-session harder than within-session.
        seed: base seed; each recording derives a deterministic seed from it.
    """

    name = "synthetic_drift"

    def __init__(
        self,
        n_subjects: int = 3,
        n_sessions: int = 4,
        n_channels: int = 2,
        sample_rate: float = 1000.0,
        block_seconds: float = 1.0,
        n_blocks: int = 6,
        drift_per_session: float = 0.25,
        seed: int = 0,
    ) -> None:
        self.n_subjects = n_subjects
        self.n_sessions = n_sessions
        self.n_channels = n_channels
        self.sample_rate = sample_rate
        self.block_seconds = block_seconds
        self.n_blocks = n_blocks
        self.drift_per_session = drift_per_session
        self.seed = seed

    def subjects(self) -> list[str]:
        return [f"s{i + 1:02d}" for i in range(self.n_subjects)]

    def session_ids(self) -> list[str]:
        return [f"d{i + 1:02d}" for i in range(self.n_sessions)]

    def load(
        self, subjects: Sequence[str] | None = None, sessions: Sequence[str] | None = None
    ) -> Iterator[EmgRecording]:
        wanted_subjects = list(subjects) if subjects is not None else self.subjects()
        wanted_sessions = list(sessions) if sessions is not None else self.session_ids()
        for subject in wanted_subjects:
            for session in wanted_sessions:
                yield self._make(subject, session)

    def _make(self, subject: str, session: str) -> EmgRecording:
        subject_index = self.subjects().index(subject)
        session_index = self.session_ids().index(session)
        rng = np.random.default_rng([self.seed, subject_index, session_index])

        block = int(self.block_seconds * self.sample_rate)
        gain = 1.0 + self.drift_per_session * session_index
        offset = 0.002 * session_index
        subject_gain = 1.0 + 0.1 * subject_index

        chunks: list[np.ndarray] = []
        labels: list[np.ndarray] = []
        for _ in range(self.n_blocks):
            for label, amplitude in ((0, 0.01), (1, 0.06)):
                noise = rng.standard_normal((block, self.n_channels))
                chunks.append(amplitude * gain * subject_gain * noise + offset)
                labels.append(np.full(block, label, dtype=int))

        return EmgRecording(
            signal=np.concatenate(chunks, axis=0),
            sample_rate=self.sample_rate,
            labels=np.concatenate(labels),
            subject_id=subject,
            session_id=session,
            source=self.name,
            meta={"fixture": True, "session_gain": gain, "session_offset": offset},
        )
