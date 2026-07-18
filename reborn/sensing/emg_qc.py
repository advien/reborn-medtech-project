"""EMG signal-quality checks.

Two layers live here, on purpose:

* `check_dropout` / `check_saturation` / `assess_quality` — the conservative,
  always-on pair the **safety** path relies on (see `sim/run_baseline_loop.py`,
  `reborn/safety/fault_detection.py`). Their behaviour is deliberately stable:
  promoting a new check into this path changes *when the system trusts EMG*, which
  is a safety decision made deliberately, not a side effect.
* The richer deterministic checks and `assess_quality_report` — an analysis layer
  for notebook 01 and as feature/label source for the advisory
  `reborn.ml.anomaly` detector. These are label-free heuristics, one per named
  failure mode from `docs/research/research-context.md` §5.3.

The direct ML contribution (`reborn.ml.anomaly`, phase B) is meant to go *beyond*
what these catch, not replace them; the heuristics stay as a cheap first line.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# --------------------------------------------------------------------------- #
# Safety-path checks — stable interface, do not change behaviour lightly.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class SignalQuality:
    valid: bool
    reason: str | None = None


def check_dropout(x: np.ndarray, flatline_std: float = 1e-6) -> SignalQuality:
    """Flatline / dropout: signal variance collapses (lead-off, disconnect)."""
    if float(np.std(x)) < flatline_std:
        return SignalQuality(valid=False, reason="dropout")
    return SignalQuality(valid=True)


def check_saturation(x: np.ndarray, limit: float = 1.0, max_fraction: float = 0.05) -> SignalQuality:
    """Saturation: too large a fraction of samples sit at/over the rail."""
    saturated_fraction = float(np.mean(np.abs(x) >= limit))
    if saturated_fraction > max_fraction:
        return SignalQuality(valid=False, reason="saturation")
    return SignalQuality(valid=True)


def assess_quality(x: np.ndarray, saturation_limit: float = 1.0, flatline_std: float = 1e-6) -> SignalQuality:
    """Conservative always-on gate: first failure among dropout, saturation.

    This is the version the safety layer consumes. It intentionally does *not*
    run the richer heuristics below — see the module docstring.
    """
    dropout = check_dropout(x, flatline_std)
    if not dropout.valid:
        return dropout
    return check_saturation(x, saturation_limit)


# --------------------------------------------------------------------------- #
# Analysis-layer checks — richer failure-mode taxonomy (label-free).
# Not on the safety path; consumed by notebook 01 and reborn.ml.anomaly.
# --------------------------------------------------------------------------- #


def check_clipping(x: np.ndarray, limit: float = 1.0, min_run: int = 5) -> SignalQuality:
    """Flat-topped clipping: a run of consecutive samples pinned at the rail.

    Distinct from `check_saturation` (which only counts the *fraction* over the
    rail): a long flat run at the extreme is the tell-tale of hard clipping even
    when the overall fraction is small.
    """
    pinned = np.abs(x) >= limit
    if not pinned.any():
        return SignalQuality(valid=True)
    # longest consecutive run of pinned samples
    longest = _longest_true_run(pinned)
    if longest >= min_run:
        return SignalQuality(valid=False, reason="clipping")
    return SignalQuality(valid=True)


def check_dropout_run(
    x: np.ndarray, near_zero: float | None = None, min_run: int = 10
) -> SignalQuality:
    """Partial dropout: a long contiguous run of near-zero samples inside a window.

    `check_dropout` looks at whole-window variance (right for the small per-frame
    windows the safety path sees); over a longer analysis window a *partial*
    flatline leaves overall variance high, so we look for a near-zero run instead.
    `near_zero` defaults to 1% of the window's std.
    """
    x = np.asarray(x, dtype=float).reshape(-1)
    if near_zero is None:
        near_zero = max(1e-6, 0.01 * float(np.std(x)))
    quiet = np.abs(x) < near_zero
    if _longest_true_run(quiet) >= min_run:
        return SignalQuality(valid=False, reason="dropout")
    return SignalQuality(valid=True)


def check_amplitude_range(
    x: np.ndarray, min_rms: float = 1e-3, max_rms: float = 5.0
) -> SignalQuality:
    """Out-of-range amplitude: channel effectively dead (too low) or absurd (too high)."""
    r = float(np.sqrt(np.mean(np.square(x))))
    if r < min_rms:
        return SignalQuality(valid=False, reason="amplitude_low")
    if r > max_rms:
        return SignalQuality(valid=False, reason="amplitude_high")
    return SignalQuality(valid=True)


def check_baseline_offset(x: np.ndarray, max_offset: float = 0.2) -> SignalQuality:
    """Baseline/DC offset: a large mean suggests electrode/baseline drift.

    Surface EMG is near zero-mean after band-pass; a persistent offset flags a
    conditioning or contact problem.
    """
    if abs(float(np.mean(x))) > max_offset:
        return SignalQuality(valid=False, reason="baseline_offset")
    return SignalQuality(valid=True)


def check_powerline(
    x: np.ndarray,
    sample_rate: float,
    mains_hz: float = 50.0,
    max_ratio: float = 0.5,
    band_hz: float = 5.0,
) -> SignalQuality:
    """Mains interference: fraction of power within +/-band of the mains line.

    Requires a sample rate. High ratio => 50/60 Hz pickup dominates (poor
    grounding / loose electrode). Uses Welch PSD; scipy is already a core dep.
    """
    from scipy import signal as _sig
    from scipy.integrate import trapezoid

    n = int(np.asarray(x).size)
    if n < 16 or sample_rate <= 2 * mains_hz:
        return SignalQuality(valid=True)  # too short / rate too low to judge
    nperseg = min(1024, n)
    freqs, psd = _sig.welch(x, fs=sample_rate, nperseg=nperseg)
    total = float(trapezoid(psd, freqs))
    if total <= 0.0:
        return SignalQuality(valid=True)
    band = (freqs >= mains_hz - band_hz) & (freqs <= mains_hz + band_hz)
    mains_power = float(trapezoid(psd[band], freqs[band])) if band.any() else 0.0
    if mains_power / total > max_ratio:
        return SignalQuality(valid=False, reason="powerline")
    return SignalQuality(valid=True)


@dataclass(frozen=True)
class QualityReport:
    """Aggregate result of all applicable analysis-layer checks."""

    valid: bool
    failures: tuple[str, ...] = ()
    metrics: dict[str, float] = field(default_factory=dict)


def assess_quality_report(
    x: np.ndarray,
    sample_rate: float | None = None,
    saturation_limit: float = 1.0,
    flatline_std: float = 1e-6,
    clip_min_run: int = 5,
    min_rms: float = 1e-3,
    max_rms: float = 5.0,
    max_offset: float = 0.2,
    mains_hz: float = 50.0,
    max_powerline_ratio: float = 0.5,
) -> QualityReport:
    """Run every applicable check and return all failures plus computed metrics.

    This is the analysis entry point (notebook 01), separate from the safety
    path `assess_quality`. `check_powerline` runs only when `sample_rate` is given.
    """
    x = np.asarray(x, dtype=float).reshape(-1)
    checks = [
        check_dropout(x, flatline_std),
        check_dropout_run(x),
        check_saturation(x, saturation_limit),
        check_clipping(x, saturation_limit, clip_min_run),
        check_amplitude_range(x, min_rms, max_rms),
        check_baseline_offset(x, max_offset),
    ]
    if sample_rate is not None:
        checks.append(check_powerline(x, sample_rate, mains_hz, max_powerline_ratio))

    reasons = [c.reason for c in checks if not c.valid and c.reason is not None]
    failures = tuple(dict.fromkeys(reasons))  # de-duplicated, order preserved

    metrics: dict[str, float] = {
        "std": float(np.std(x)),
        "rms": float(np.sqrt(np.mean(np.square(x)))),
        "mav": float(np.mean(np.abs(x))),
        "dc_offset": float(np.mean(x)),
        "saturated_fraction": float(np.mean(np.abs(x) >= saturation_limit)),
        "max_clip_run": float(_longest_true_run(np.abs(x) >= saturation_limit)),
    }
    return QualityReport(valid=len(failures) == 0, failures=failures, metrics=metrics)


def _longest_true_run(mask: np.ndarray) -> int:
    """Length of the longest run of consecutive True values in a boolean array."""
    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        return 0
    # difference of cumulative sums at reset points gives run lengths
    longest = run = 0
    for v in mask:
        run = run + 1 if v else 0
        if run > longest:
            longest = run
    return int(longest)
