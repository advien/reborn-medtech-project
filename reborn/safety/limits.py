"""Hard torque/velocity/angle limits. These are the last line of defense and
are enforced regardless of what upstream logic requests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyLimits:
    max_torque: float = 5.0      # Nm
    max_velocity: float = 3.0    # rad/s
    min_angle: float = 0.0       # rad
    max_angle: float = 2.35      # rad (~135 degrees of elbow flexion)


def clamp_torque(torque: float, limits: SafetyLimits) -> float:
    return max(-limits.max_torque, min(limits.max_torque, torque))


def check_angle(angle: float, limits: SafetyLimits) -> bool:
    return limits.min_angle <= angle <= limits.max_angle


def check_velocity(velocity: float, limits: SafetyLimits) -> bool:
    return abs(velocity) <= limits.max_velocity


def enforce(torque: float, angle: float, velocity: float, limits: SafetyLimits) -> float:
    """Returns a torque command guaranteed to respect all hard limits.

    If angle or velocity are already out of bounds, returns 0 torque instead of
    raising — the safety layer degrades to "no assist," it does not hand control
    back to the caller mid-loop.
    """
    if not check_angle(angle, limits) or not check_velocity(velocity, limits):
        return 0.0
    return clamp_torque(torque, limits)
