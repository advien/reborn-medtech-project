"""1-DOF elbow (pendulum) dynamics — placeholder.

TODO(phase C, docs/roadmap.md topic 3): replace with a real 1-DOF pendulum
model under variable external load. The current implementation is a linear
integrator with viscous damping and a mechanical hard stop so the baseline
loop has something to drive end-to-end; it is not biomechanically meaningful.

The hard stop is not a stand-in for `reborn.safety` — real orthoses have a
physical end-of-range stop independent of any control decision, and a
zero-torque command alone can't arrest existing velocity without one.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ElbowState:
    angle: float = 0.0     # rad
    velocity: float = 0.0  # rad/s


class ElbowModel:
    def __init__(self, inertia: float = 0.05, damping: float = 0.3, hard_stop_angle: float = 2.5) -> None:
        self.inertia = inertia
        self.damping = damping
        self.hard_stop_angle = hard_stop_angle
        self.state = ElbowState()

    def step(self, torque: float, dt: float) -> ElbowState:
        acceleration = (torque - self.damping * self.state.velocity) / self.inertia
        self.state.velocity += acceleration * dt
        self.state.angle += self.state.velocity * dt

        if abs(self.state.angle) > self.hard_stop_angle:
            self.state.angle = max(-self.hard_stop_angle, min(self.hard_stop_angle, self.state.angle))
            self.state.velocity = 0.0

        return self.state
