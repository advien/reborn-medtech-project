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


class NinaproDB6Loader(DatasetLoader):
    """Reads DB6 `.mat` files into canonical recordings.

    Args:
        root: directory holding the `.mat` files (searched recursively).
        pattern: compiled regex with named groups `subject`, `day`, `session`.
        label_field: `restimulus` is the re-labelled (movement-aligned) stimulus
            and is the right default; `stimulus` is the raw prompt and lags the
            actual movement, which biases any latency-sensitive result.
        sample_rate: native rate, 2 kHz for DB6.
    """

    name = "ninapro_db6"

    def __init__(
        self,
        root: str | Path,
        pattern: re.Pattern[str] = DEFAULT_PATTERN,
        label_field: str = "restimulus",
        sample_rate: float = NATIVE_SAMPLE_RATE,
    ) -> None:
        self.root = Path(root)
        self.pattern = pattern
        self.label_field = label_field
        self.sample_rate = sample_rate

    # ----------------------------------------------------------------- #

    def files(self) -> list[Path]:
        if not self.root.is_dir():
            raise FileNotFoundError(
                f"{self.root} does not exist — download Ninapro DB6 into it first (data/README.md)"
            )
        found = sorted(self.root.rglob("*.mat"))
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

        # DB6 encodes rest as 0, which is already reborn.data.records.REST_LABEL.
        return EmgRecording(
            signal=signal,
            sample_rate=self.sample_rate,
            labels=labels,
            subject_id=subject,
            session_id=session,
            source=self.name,
            meta={"path": str(path), "label_field": self.label_field},
        )
