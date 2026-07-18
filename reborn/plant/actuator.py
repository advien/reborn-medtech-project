"""Actuator model with saturation and slew-rate limits — placeholder.

TODO(phase C, docs/roadmap.md topic 5): model realistic actuator dynamics
(bandwidth, backlash) as part of the robust-control-under-saturation work.
Today this only clamps torque and rate of change, mirroring
reborn.safety.limits.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActuatorLimits:
    max_torque: float = 5.0  # Nm
    max_rate: float = 20.0   # Nm/s


class ActuatorModel:
    def __init__(self, limits: ActuatorLimits | None = None) -> None:
        self.limits = limits or ActuatorLimits()
        self._last_torque = 0.0

    def apply(self, requested_torque: float, dt: float) -> float:
        max_delta = self.limits.max_rate * dt
        delta = max(-max_delta, min(max_delta, requested_torque - self._last_torque))
        torque = self._last_torque + delta
        torque = max(-self.limits.max_torque, min(self.limits.max_torque, torque))
        self._last_torque = torque
        return torque
