"""Closed-loop control of the elbow model under variable load — skeleton.

TODO(phase C, docs/roadmap.md topic 3): implement, consuming
reborn.plant.elbow_model and reborn.plant.actuator.
"""

from __future__ import annotations


class ClosedLoopController:
    def __init__(self) -> None:
        raise NotImplementedError("Phase C work — see docs/roadmap.md, topic 3.")

    def step(self, setpoint: float, measurement: float, dt: float) -> float:
        raise NotImplementedError
