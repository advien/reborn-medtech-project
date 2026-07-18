"""Hardware abstraction layer interfaces — the spine of Reborn.

Everything outside `reborn.hal` (sensing, decision, safety, control, ml) depends
only on `SensorSource` and `ActuatorSink`. Swapping simulation for hardware means
constructing a different backend (see `sim_backend.py` / `hardware_backend.py`)
and passing it in — nothing above this layer changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(frozen=True)
class SensorFrame:
    """One timestep of sensor data.

    `valid` reflects hardware/sim-level validity (e.g. a dropped serial packet),
    independent of the signal-quality checks in `reborn.sensing.emg_qc`, which
    assess whether valid-but-noisy data is still usable.
    """

    timestamp: float
    emg: np.ndarray
    imu: dict[str, float] | None = None
    valid: bool = True


@dataclass(frozen=True)
class ActuatorCommand:
    """A single actuator setpoint."""

    timestamp: float
    torque: float
    meta: dict[str, Any] = field(default_factory=dict)


class SensorSource(ABC):
    """Something that produces a stream of `SensorFrame`s."""

    @abstractmethod
    def read(self) -> SensorFrame | None:
        """Return the next sensor frame, or None if the stream is exhausted."""

    def close(self) -> None:
        """Release any underlying resources. Default: no-op."""


class ActuatorSink(ABC):
    """Something that consumes `ActuatorCommand`s."""

    @abstractmethod
    def send(self, command: ActuatorCommand) -> None:
        """Send a command to the actuator."""

    def close(self) -> None:
        """Release any underlying resources. Default: no-op."""
