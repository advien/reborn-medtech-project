"""Deterministic, safety-relevant state machine for the Reborn control loop.

States and transitions follow docs/safety.md. Transitions are intentionally
conservative: low confidence or a failed safety check can only ever move the
system toward a *less* active state. FALLBACK and EMERGENCY_STOP both require
an explicit `reset()` — the system never talks itself back into assisting.
"""

from __future__ import annotations

from enum import Enum, auto


class SystemState(Enum):
    IDLE = auto()
    ASSIST = auto()
    DEGRADED = auto()
    FALLBACK = auto()
    EMERGENCY_STOP = auto()


class StateMachine:
    def __init__(self) -> None:
        self._state = SystemState.IDLE

    @property
    def state(self) -> SystemState:
        return self._state

    def step(self, *, intent: bool, confidence: float, safety_ok: bool, emergency: bool = False) -> SystemState:
        """Advance the state machine by one control-loop tick.

        `confidence` is expected in [0, 1]. `safety_ok` is the combined result of
        `reborn.safety` checks for this tick; `emergency` is a hard override
        (e.g. an unrecoverable fault) that always wins.
        """
        if emergency:
            self._state = SystemState.EMERGENCY_STOP
            return self._state

        if self._state in (SystemState.EMERGENCY_STOP, SystemState.FALLBACK):
            return self._state  # requires explicit reset()

        if not safety_ok:
            self._state = SystemState.FALLBACK
            return self._state

        if intent and confidence >= 0.7:
            self._state = SystemState.ASSIST
        elif intent and confidence >= 0.4:
            self._state = SystemState.DEGRADED
        else:
            self._state = SystemState.IDLE

        return self._state

    def reset(self) -> SystemState:
        """Explicitly clear FALLBACK/EMERGENCY_STOP back to IDLE."""
        self._state = SystemState.IDLE
        return self._state
