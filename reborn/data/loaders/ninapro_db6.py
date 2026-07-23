"""Ninapro DB6 — the primary cross-session dataset for phase B.

DB6 was built to study **repeatability**: 10 intact subjects, 14 Delsys Trigno
double-differential electrodes on the forearm at 2 kHz, 7 activities-of-daily-
living grasps repeated 12 times per session, two sessions a day across 5 days —
10 sessions per subject. That structure is why it is the primary dataset here:
session is a cleanly controlled factor with everything else held fixed
(`docs/research/phase-b-plan.md` §3).

Data is not committed. Download to `data/ninapro_db6/` exactly as distributed
(`data/README.md`) and point the loader at that directory.

**Filename convention.** Ninapro distributions have varied their naming across
databases and re-releases, so the pattern is a parameter rather than an
assumption: the default matches `S<subject>_D<day>_T<session>` and the loader
raises with the filenames it actually found rather than silently mis-parsing
them. Verify against your download before trusting any cross-session number —
a mis-parsed session id turns the cross-session protocol into a within-session
one without any error appearing.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator, Sequence

import numpy as np

from ..records import EmgRecording
from .base import DatasetLoader

DEFAULT_PATTERN = re.compile(r"S(?P<subject>\d+)_D(?P<day>\d+)_T(?P<session>\d+)", re.IGNORECASE)
NATIVE_SAMPLE_RATE = 2000.0

PADDING_CHANNELS = (8, 9)
"""Columns that are identically zero in every DB6 file.

`emg` is a 16-column array but DB6 records 14 electrodes; columns 8 and 9 are
padding, verified constant-zero across subjects and sessions. They are dropped
by default because the QC gate rejects a window when *any* inspected channel
fails — leaving the padding in place rejects 100% of windows for a reason that
has nothing to do with signal quality."""

DEFAULT_CHANNELS = tuple(c for c in range(16) if c not in PADDING_CHANNELS)


class NinaproDB6Loader(DatasetLoader):
    """Reads DB6 `.mat` files into canonical recordings.

    Args:
        root: directory holding the `.mat` files (searched recursively).
        pattern: compiled regex with named groups `subject`, `day`, `session`.
        label_field: `restimulus` is the re-labelled (movement-aligned) stimulus
            and is the right default; `stimulus` is the raw prompt and lags the
            actual movement, which biases any latency-sensitive result.
        channels: column indices to keep. Defaults to everything but the padding
            columns (see `PADDING_CHANNELS`). Narrow this to the montage that
            mirrors the target hardware — Reborn has one or two channels, so
            gating on fourteen forearm electrodes models a different system, and
            the full set is also what makes a QC pass over the whole dataset
            slow.
        sample_rate: native rate, 2 kHz for DB6.
    """

    name = "ninapro_db6"

    def __init__(
        self,
        root: str | Path,
        pattern: re.Pattern[str] = DEFAULT_PATTERN,
        label_field: str = "restimulus",
        channels: Sequence[int] | None = DEFAULT_CHANNELS,
        sample_rate: float = NATIVE_SAMPLE_RATE,
    ) -> None:
        self.root = Path(root)
        self.pattern = pattern
        self.label_field = label_field
        self.channels = tuple(channels) if channels is not None else None
        self.sample_rate = sample_rate

    # ----------------------------------------------------------------- #

    def files(self) -> list[Path]:
        if not self.root.is_dir():
            raise FileNotFoundError(
                f"{self.root} does not exist — download Ninapro DB6 into it first (data/README.md)"
            )
        # The distributed archives are zipped on macOS, so they carry __MACOSX
        # AppleDouble stubs alongside the real files; those are not readable MAT
        # files and would crash loadmat.
        found = sorted(
            p
            for p in self.root.rglob("*.mat")
            if not p.name.startswith("._") and "__MACOSX" not in p.parts
        )
        if not found:
            raise FileNotFoundError(f"no .mat files under {self.root}")
        return found

    def index(self) -> list[tuple[str, str, Path]]:
        """`(subject_id, session_id, path)` for every parseable file."""
        entries: list[tuple[str, str, Path]] = []
        unparsed: list[str] = []
        for path in self.files():
            match = self.pattern.search(path.stem)
            if match is None:
                unparsed.append(path.name)
                continue
            subject = f"s{int(match.group('subject')):02d}"
            # Zero-padded and day-major so lexicographic order is chronological —
            # cross_session_splits sorts session ids to order them in time.
            session = f"d{int(match.group('day')):02d}_t{int(match.group('session')):02d}"
            entries.append((subject, session, path))
        if not entries:
            raise ValueError(
                f"none of the {len(unparsed)} .mat files under {self.root} matched "
                f"{self.pattern.pattern!r}. Found e.g. {unparsed[:5]}. Pass a `pattern` that "
                "matches this distribution's naming — see the module docstring."
            )
        return sorted(entries)

    def subjects(self) -> list[str]:
        return sorted({subject for subject, _, _ in self.index()})

    def load(
        self, subjects: Sequence[str] | None = None, sessions: Sequence[str] | None = None
    ) -> Iterator[EmgRecording]:
        wanted_subjects = set(subjects) if subjects is not None else None
        wanted_sessions = set(sessions) if sessions is not None else None
        for subject, session, path in self.index():
            if wanted_subjects is not None and subject not in wanted_subjects:
                continue
            if wanted_sessions is not None and session not in wanted_sessions:
                continue
            yield self._read(subject, session, path)

    # ----------------------------------------------------------------- #

    def _read(self, subject: str, session: str, path: Path) -> EmgRecording:
        from scipy.io import loadmat  # local import: only needed when real data is present

        mat = loadmat(path, squeeze_me=False)
        if "emg" not in mat:
            raise KeyError(f"{path.name} has no 'emg' variable (keys: {sorted(mat)})")
        if self.label_field not in mat:
            raise KeyError(
                f"{path.name} has no {self.label_field!r} variable (keys: {sorted(mat)}); "
                "pass label_field='stimulus' if this distribution lacks restimulus"
            )
        signal = np.asarray(mat["emg"], dtype=float)
        labels = np.asarray(mat[self.label_field]).reshape(-1).astype(int)

        # DB6 presents each grasp as a contiguous block of 12 repetitions, not
        # interleaved, so a temporal within-session split would put whole classes
        # on one side of the train/test line. `rerepetition` is what makes a
        # repetition-wise split possible — the Ninapro convention.
        repetition_field = "rerepetition" if self.label_field == "restimulus" else "repetition"
        repetitions = (
            np.asarray(mat[repetition_field]).reshape(-1).astype(int)
            if repetition_field in mat
            else None
        )

        channels = self.channels
        if channels is not None:
            if max(channels) >= signal.shape[1]:
                raise ValueError(
                    f"{path.name} has {signal.shape[1]} columns; requested channel "
                    f"{max(channels)}. Pass `channels` matching this distribution."
                )
            signal = signal[:, list(channels)]

        # DB6 encodes rest as 0, which is already reborn.data.records.REST_LABEL.
        return EmgRecording(
            signal=signal,
            sample_rate=self.sample_rate,
            labels=labels,
            subject_id=subject,
            session_id=session,
            repetitions=repetitions,
            source=self.name,
            meta={
                "path": str(path),
                "label_field": self.label_field,
                "repetition_field": repetition_field if repetitions is not None else None,
                "channels": list(channels) if channels is not None else None,
            },
        )
