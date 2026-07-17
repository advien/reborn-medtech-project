"""Fallback policy selection: safe idle / passive / limited assist.

`select_fallback` never chooses more assist than the situation warrants — a
fault always dominates a merely-low confidence score.
"""

from __future__ import annotations

from enum import Enum, auto


class FallbackMode(Enum):
    NONE = auto()
    LIMITED_ASSIST = auto()
    PASSIVE = auto()


def select_fallback(*, faulted: bool, confidence: float) -> FallbackMode:
    if faulted:
        return FallbackMode.PASSIVE
    if confidence < 0.4:
        return FallbackMode.LIMITED_ASSIST
    return FallbackMode.NONE
