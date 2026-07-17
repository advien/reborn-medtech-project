"""Hardware backend for a real MyoWare EMG + IMU sensor rig and an
Arduino-driven actuator — the phase-2 (hardware) engineering stage.

Not implemented yet. Implementing this file (over `pyserial` or similar) should
be the *only* change needed to move the rest of the system from simulation to
real hardware, since everything above the HAL depends only on
`reborn.hal.interfaces`. See docs/roadmap.md, stage 2.
"""

from __future__ import annotations

from reborn.hal.interfaces import ActuatorCommand, ActuatorSink, SensorFrame, SensorSource


class HardwareSensorSource(SensorSource):
    def __init__(self, port: str, baud_rate: int = 115200) -> None:
        raise NotImplementedError(
            "Hardware sensing (MyoWare EMG + IMU over serial) is not implemented "
            "yet — see docs/roadmap.md, stage 2 (hardware)."
        )

    def read(self) -> SensorFrame | None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class HardwareActuatorSink(ActuatorSink):
    def __init__(self, port: str, baud_rate: int = 115200) -> None:
        raise NotImplementedError(
            "Hardware actuation (Arduino-driven servo) is not implemented yet — "
            "see docs/roadmap.md, stage 2 (hardware)."
        )

    def send(self, command: ActuatorCommand) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError
