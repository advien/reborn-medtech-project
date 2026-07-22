"""The dataset-agnostic loading interface.

Each public EMG dataset gets one backend behind this interface, all returning
`EmgRecording`. The reason is not tidiness: the phase-B datasets each isolate a
*different* controlled variable (session, subject, hardware — see
`docs/research/phase-b-plan.md` §3), so protocols and metrics have to be written
once and pointed at whichever dataset isolates the factor under test. A script
per dataset would make those results incomparable.

This layer is **offline and research-side**. It is not part of the runtime
control loop and must not be imported by `reborn.decision`, `reborn.safety`, or
`reborn.control` — the HAL is the only path sensor data reaches those. Replaying
a recording through a `SensorSource` for phase C is a separate, later bridge.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator, Sequence

from ..records import EmgRecording


class DatasetLoader(ABC):
    """Something that yields `EmgRecording`s from a locally downloaded dataset."""

    name: str = ""

    @abstractmethod
    def subjects(self) -> list[str]:
        """Subject identifiers available locally, sorted."""

    @abstractmethod
    def load(
        self, subjects: Sequence[str] | None = None, sessions: Sequence[str] | None = None
    ) -> Iterator[EmgRecording]:
        """Yield recordings, optionally restricted to given subjects/sessions.

        Yields rather than returns: the phase-B datasets are tens of gigabytes and
        the pipeline consumes recordings one at a time.
        """
