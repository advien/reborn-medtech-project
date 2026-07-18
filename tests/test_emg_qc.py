"""Tests for EMG signal-quality checks (reborn.sensing.emg_qc).

Each analysis-layer check is exercised against the matching corruption model in
reborn.sensing.corruption: inject a known fault, confirm the detector catches it,
and confirm a clean signal passes. The safety-path `assess_quality` is checked
for behavioural stability (dropout + saturation only).
"""

from __future__ import annotations

import numpy as np
import pytest

from reborn.sensing import corruption
from reborn.sensing.emg_qc import (
    assess_quality,
    assess_quality_report,
    check_amplitude_range,
    check_baseline_offset,
    check_clipping,
    check_dropout,
    check_powerline,
    check_saturation,
)

RATE = 1000.0


def clean_emg(n: int = 1000, seed: int = 0) -> np.ndarray:
    """A modest zero-mean band-limited-ish signal standing in for clean EMG."""
    rng = np.random.default_rng(seed)
    return 0.1 * rng.standard_normal(n)


# --------------------------------------------------------------------------- #
# Safety-path stability
# --------------------------------------------------------------------------- #


def test_assess_quality_passes_clean_signal():
    assert assess_quality(clean_emg()).valid


def test_assess_quality_flags_dropout():
    q = assess_quality(np.zeros(1000))
    assert not q.valid and q.reason == "dropout"


def test_assess_quality_flags_saturation():
    # A *varying* over-driven signal: has non-zero std (so it isn't caught as
    # dropout) but many samples sit at the rail.
    x = corruption.inject_saturation(clean_emg(), limit=1.0, gain=50.0)
    q = assess_quality(x)
    assert not q.valid and q.reason == "saturation"


# --------------------------------------------------------------------------- #
# Individual analysis-layer checks vs. their corruption model
# --------------------------------------------------------------------------- #


def test_dropout_detects_injected_flatline():
    x = corruption.inject_dropout(clean_emg(), start=0.0, length=1.0)
    assert not check_dropout(x).valid


def test_saturation_detects_injected_saturation():
    x = corruption.inject_saturation(clean_emg(), limit=1.0, gain=50.0)
    assert not check_saturation(x).valid


def test_clipping_detects_flat_run_that_saturation_fraction_misses():
    # A short clipped run: fraction over the rail is tiny, but the flat run is long.
    x = corruption.inject_clipping(clean_emg(2000), limit=1.0, start=0.3, length=0.02)
    assert not check_clipping(x, limit=1.0, min_run=5).valid
    # the fraction-based saturation check is happy with such a small fraction
    assert check_saturation(x, limit=1.0, max_fraction=0.05).valid


def test_amplitude_range_flags_dead_and_absurd():
    assert check_amplitude_range(np.full(500, 1e-5)).reason == "amplitude_low"
    assert check_amplitude_range(np.full(500, 100.0)).reason == "amplitude_high"
    assert check_amplitude_range(clean_emg()).valid


def test_baseline_offset_detects_dc():
    x = corruption.inject_baseline_offset(clean_emg(), offset=0.5)
    assert not check_baseline_offset(x, max_offset=0.2).valid
    assert check_baseline_offset(clean_emg(), max_offset=0.2).valid


def test_powerline_detects_mains_component():
    t = np.arange(2000) / RATE
    mains = np.sin(2 * np.pi * 50.0 * t)  # pure 50 Hz dominates
    assert not check_powerline(mains, RATE, mains_hz=50.0).valid
    assert check_powerline(clean_emg(2000), RATE, mains_hz=50.0).valid


def test_powerline_short_signal_is_not_judged():
    assert check_powerline(clean_emg(8), RATE).valid  # too short -> pass


# --------------------------------------------------------------------------- #
# Aggregate report
# --------------------------------------------------------------------------- #


def test_report_clean_signal_has_no_failures():
    r = assess_quality_report(clean_emg(), sample_rate=RATE)
    assert r.valid and r.failures == ()
    assert set(r.metrics) >= {"std", "rms", "mav", "dc_offset"}


def test_report_collects_multiple_failures():
    x = corruption.inject_baseline_offset(np.zeros(1000), offset=0.5)  # dropout-ish + offset
    r = assess_quality_report(x)
    assert not r.valid
    assert "baseline_offset" in r.failures


# The deterministic report is responsible for the "hard", rule-nameable modes.
# A broadband `noise_burst` is deliberately NOT in this list — catching
# "this doesn't look like normal EMG" is the advisory anomaly detector's job
# (see tests/test_anomaly.py), not a fixed threshold's.
DETERMINISTIC_MODES = ("dropout", "saturation", "clipping", "baseline_offset")


@pytest.mark.parametrize("mode", DETERMINISTIC_MODES)
def test_deterministic_report_flags_hard_fault_modes(mode):
    x = corruption.corrupt(clean_emg(2000), mode)
    r = assess_quality_report(x, sample_rate=RATE)
    assert not r.valid, f"{mode} slipped past every deterministic check"
