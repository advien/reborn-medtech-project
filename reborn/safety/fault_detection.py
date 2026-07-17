"""Detects dropout, latency spikes, and sensor desynchronization.

Minimal checks needed to drive `reborn.safety.fallback` decisions in the
baseline loop, matching the triggers listed in docs/safety.md. Not a full
watchdog implementation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FaultReport:
    faulted: bool
    reason: str | None = None


class FaultDetector:
    def __init__(self, max_latency_s: float = 0.05, max_missed_frames: int = 3) -> None:
        self.max_latency_s = max_latency_s
        self.max_missed_frames = max_missed_frames
        self._missed_frames = 0

    def check_frame(self, *, frame_valid: bool, latency_s: float) -> FaultReport:
        self._missed_frames = 0 if frame_valid else self._missed_frames + 1

        if self._missed_frames >= self.max_missed_frames:
            return FaultReport(faulted=True, reason="dropout")
        if latency_s > self.max_latency_s:
            return FaultReport(faulted=True, reason="latency")
        return FaultReport(faulted=False)

    def check_desync(self, *, emg_timestamp: float, imu_timestamp: float, max_skew_s: float = 0.02) -> FaultReport:
        if abs(emg_timestamp - imu_timestamp) > max_skew_s:
            return FaultReport(faulted=True, reason="desync")
        return FaultReport(faulted=False)
