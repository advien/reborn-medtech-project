"""Deterministic EMG corruption models — for *validating detectors*, not a data source.

Each function takes a clean signal and injects one named failure mode from
`docs/research/research-context.md` §5.3, returning the corrupted copy. They are
the inverse of the checks in `reborn.sensing.emg_qc`: given a known injected
fault, a working detector must catch it.

Why this exists, and its boundary:

* Legitimate use — unit-testing QC/anomaly detectors and building the labelled
  fault set in notebook 01 (inject a known fault -> confirm it is detected).
* NOT legitimate — presenting corrupted-synthetic signals as a *result* about
  real EMG. Per the roadmap's "real data, not synthetic" principle, quantitative
  claims must come from replayed public-dataset recordings. These helpers only
  exercise the detection machinery; the clean base they corrupt should ultimately
  be a real recording (Ninapro), with synthetic bases used only for smoke tests.
"""

from __future__ import annotations

import numpy as np

FAULT_MODES = ("dropout", "saturation", "clipping", "baseline_offset", "noise_burst")


def inject_dropout(x: np.ndarray, start: float = 0.4, length: float = 0.2) -> np.ndarray:
    """Flatline a contiguous fraction of the window (lead-off / disconnect)."""
    x = np.array(x, dtype=float)
    i0, i1 = _span(x.size, start, length)
    x[i0:i1] = 0.0
    return x


def inject_saturation(x: np.ndarray, limit: float = 1.0, gain: float = 10.0) -> np.ndarray:
    """Over-drive and hard-limit the whole window so many samples hit the rail."""
    x = np.array(x, dtype=float)
    return np.clip(x * gain, -limit, limit)


def inject_clipping(
    x: np.ndarray, limit: float = 1.0, start: float = 0.3, length: float = 0.1
) -> np.ndarray:
    """Pin a short contiguous run at the positive rail (flat-topped clipping)."""
    x = np.array(x, dtype=float)
    i0, i1 = _span(x.size, start, length)
    x[i0:i1] = limit
    return x


def inject_baseline_offset(x: np.ndarray, offset: float = 0.5) -> np.ndarray:
    """Add a persistent DC offset (baseline / contact drift)."""
    return np.array(x, dtype=float) + offset


def inject_noise_burst(
    x: np.ndarray, amplitude: float = 0.5, start: float = 0.5, length: float = 0.15, seed: int = 0
) -> np.ndarray:
    """Add a burst of high-amplitude broadband noise (motion artefact / interference)."""
    x = np.array(x, dtype=float)
    i0, i1 = _span(x.size, start, length)
    rng = np.random.default_rng(seed)
    x[i0:i1] += amplitude * rng.standard_normal(i1 - i0)
    return x


def corrupt(x: np.ndarray, mode: str, **kwargs) -> np.ndarray:
    """Dispatch to the injector named by `mode` (one of FAULT_MODES)."""
    injectors = {
        "dropout": inject_dropout,
        "saturation": inject_saturation,
        "clipping": inject_clipping,
        "baseline_offset": inject_baseline_offset,
        "noise_burst": inject_noise_burst,
    }
    if mode not in injectors:
        raise ValueError(f"unknown fault mode {mode!r}; expected one of {FAULT_MODES}")
    return injectors[mode](x, **kwargs)


def _span(n: int, start: float, length: float) -> tuple[int, int]:
    i0 = int(np.clip(start, 0.0, 1.0) * n)
    i1 = int(np.clip(start + length, 0.0, 1.0) * n)
    return i0, max(i1, i0 + 1)
