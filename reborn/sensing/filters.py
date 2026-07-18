"""Standard EMG preprocessing filters."""

from __future__ import annotations

import numpy as np
from scipy import signal


def bandpass_filter(
    x: np.ndarray,
    sample_rate: float,
    low_hz: float = 20.0,
    high_hz: float = 450.0,
    order: int = 4,
) -> np.ndarray:
    """Standard EMG bandpass (removes motion artefact and high-frequency noise)."""
    nyquist = 0.5 * sample_rate
    b, a = signal.butter(order, [low_hz / nyquist, high_hz / nyquist], btype="band")
    return signal.filtfilt(b, a, x)


def notch_filter(
    x: np.ndarray,
    sample_rate: float,
    notch_hz: float = 50.0,
    quality: float = 30.0,
) -> np.ndarray:
    """Removes mains-frequency interference (50/60 Hz)."""
    b, a = signal.iirnotch(notch_hz / (0.5 * sample_rate), quality)
    return signal.filtfilt(b, a, x)
