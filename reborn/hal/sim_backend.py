"""Simulation backend: replays recorded/synthetic frames, records commands.

This is the backend every `sim/*.py` script and notebook uses today. It is a
full implementation, not a stub — the `hardware_backend` counterpart is the one
still to be built.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

import numpy as np

from reborn.hal.interfaces import ActuatorCommand, ActuatorSink, SensorFrame, SensorSource


class SimSensorSource(SensorSource):
    """Replays a fixed sequence of `SensorFrame`s, e.g. loaded from a public EMG
    dataset or generated synthetically for a specific test scenario."""

    def __init__(self, frames: Iterable[SensorFrame]) -> None:
        self._frames: Iterator[SensorFrame] = iter(frames)

    def read(self) -> SensorFrame | None:
        return next(self._frames, None)


class SimActuatorSink(ActuatorSink):
    """Records every command it receives instead of driving real hardware."""

    def __init__(self) -> None:
        self.history: list[ActuatorCommand] = []

    def send(self, command: ActuatorCommand) -> None:
        self.history.append(command)


def frames_from_emg_array(
    emg: np.ndarray,
    sample_rate: float,
    imu: list[dict[str, float]] | None = None,
    valid_mask: np.ndarray | None = None,
) -> Iterator[SensorFrame]:
    """Turn a recorded/synthetic EMG array into a sequence of `SensorFrame`s.

    `emg` is shaped (n_frames, n_channels). `valid_mask`, if given, marks frames
    that should be reported as sensor-invalid (e.g. to simulate dropout).
    """
    dt = 1.0 / sample_rate
    for i, sample in enumerate(emg):
        yield SensorFrame(
            timestamp=i * dt,
            emg=np.asarray(sample),
            imu=imu[i] if imu is not None else None,
            valid=bool(valid_mask[i]) if valid_mask is not None else True,
        )
