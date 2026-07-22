"""Deriving per-dataset QC thresholds from the data itself.

The checks in `reborn.sensing.emg_qc` use **absolute** amplitude thresholds
(`min_rms`, `max_rms`, `saturation_limit`, `max_offset`). Public EMG datasets do
not share units — Ninapro's `.mat` values, a Myo armband's integers, and putEMG's
ADC counts are three different scales — so the defaults are meaningful for at
most one of them. Running the gate with the wrong scale produces a rejection rate
that looks like a result and is an artefact of units
(`docs/research/phase-b-plan.md` §5).

This module derives thresholds from a sample of the dataset and records how, so
the numbers in the paper come with their derivation rather than from a guess.

The logic: QC exists to catch **faults**, not to trim the healthy distribution.
So each threshold sits outside the observed healthy range by an explicit margin,
and the margin is a parameter, not a constant buried in code.

    py -3.11 -m reborn.data.qc_calibration data/ninapro_db6 --subjects s01
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

import numpy as np

from .pipeline import PreprocessConfig, preprocess
from .records import EmgRecording

# Amplitude checks off, so the sample describes the signal rather than a
# pre-filtered view of it.
_OPEN_GATE = {"min_rms": 0.0, "max_rms": 1e18, "max_offset": 1e18, "saturation_limit": 1e18}


@dataclass(frozen=True)
class AmplitudeProfile:
    """What the healthy signal actually looks like, per analysis window."""

    n_windows: int
    n_channels: int
    rms: np.ndarray  # (n_windows * n_channels,)
    abs_mean: np.ndarray
    abs_max: np.ndarray

    def percentiles(self, values: np.ndarray) -> dict[str, float]:
        keys = [0.1, 1, 50, 99, 99.9]
        return {f"p{k}": float(np.percentile(values, k)) for k in keys}

    def summary(self) -> dict[str, Any]:
        return {
            "n_windows": self.n_windows,
            "n_channels": self.n_channels,
            "rms": self.percentiles(self.rms),
            "abs_mean": self.percentiles(self.abs_mean),
            "abs_max": self.percentiles(self.abs_max),
        }


def profile_amplitudes(
    recordings: Iterable[EmgRecording],
    config: PreprocessConfig | None = None,
    max_windows_per_recording: int = 2000,
) -> AmplitudeProfile:
    """Measure the amplitude distribution over preprocessed windows.

    Windows are taken after resampling and filtering, because that is what the
    QC gate sees. Sampling is capped per recording so a calibration pass over a
    few subjects stays cheap.
    """
    config = config or PreprocessConfig(qc_kwargs=dict(_OPEN_GATE))
    rms: list[np.ndarray] = []
    abs_mean: list[np.ndarray] = []
    abs_max: list[np.ndarray] = []
    n_windows = 0
    n_channels = 0

    for recording in recordings:
        prepared = preprocess(recording, config)
        n_channels = prepared.n_channels
        width, stride = config.window_samples, config.stride_samples
        starts = np.arange(0, max(0, prepared.n_samples - width + 1), stride)
        if starts.size > max_windows_per_recording:
            starts = starts[
                np.linspace(0, starts.size - 1, max_windows_per_recording).astype(int)
            ]
        for start in starts:
            window = prepared.signal[start : start + width]
            rms.append(np.sqrt(np.mean(np.square(window), axis=0)))
            abs_mean.append(np.abs(np.mean(window, axis=0)))
            abs_max.append(np.max(np.abs(window), axis=0))
            n_windows += 1

    if not rms:
        raise ValueError("no windows to profile — are the recordings shorter than one window?")

    return AmplitudeProfile(
        n_windows=n_windows,
        n_channels=n_channels,
        rms=np.concatenate(rms),
        abs_mean=np.concatenate(abs_mean),
        abs_max=np.concatenate(abs_max),
    )


def suggest_qc_thresholds(
    profile: AmplitudeProfile, margin: float = 3.0, low_margin: float = 0.1
) -> dict[str, float]:
    """Thresholds placed outside the healthy range by an explicit margin.

    Args:
        margin: multiplier applied above the observed high percentiles. Larger
            means the gate only fires on clear faults.
        low_margin: fraction of the observed low percentile used for `min_rms`.
            A dead channel reads far below the quietest healthy rest window, so
            this can sit well under it without losing sensitivity.

    These are a **starting point**, not an answer: confirm against the resulting
    rejection rate, and against faults injected with `reborn.sensing.corruption`.
    A threshold set that rejects nothing on corrupted data is not calibrated.

    **Profile the montage you will actually gate on.** The low percentiles are
    pooled across channels, so one chronically weak electrode drags `min_rms` and
    `flatline_std` down far enough that the gate can no longer tell a weak
    electrode from a working one. On Ninapro DB6 the strongest and weakest
    channels differ by a factor of ~40, and calibrating across all fourteen
    produces thresholds that are meaningless for any of them.
    """
    low = float(np.percentile(profile.rms, 0.1))
    return {
        "min_rms": low * low_margin,
        # check_dropout compares the window's standard deviation against this;
        # for the near-zero-mean signal EMG becomes after band-pass, std tracks
        # RMS, so the same reference applies. It is absolute, hence calibrated —
        # leaving it at its default is what rejects an entire dataset at once.
        "flatline_std": low * low_margin,
        "max_rms": float(np.percentile(profile.rms, 99.9) * margin),
        "max_offset": float(np.percentile(profile.abs_mean, 99.9) * margin),
        "saturation_limit": float(np.percentile(profile.abs_max, 99.9) * margin),
    }


def suggest_corruption_kwargs(profile: AmplitudeProfile, severity: float = 3.0) -> dict[str, dict]:
    """Fault-injection parameters scaled to this dataset's amplitudes.

    `reborn.sensing.corruption` takes absolute amplitudes (`limit=1.0`,
    `offset=0.5`, `amplitude=0.5`) sized for signals of order 1. DB6 samples are
    of order 1e-5, so the defaults inject faults roughly fifty thousand times
    larger than the signal — every detector catches every one of them, and the
    resulting detection rates say nothing. Feed these through `corrupt(...)`
    instead, and report the severity the rates were measured at.
    """
    rail = float(np.percentile(profile.abs_max, 99.9)) * severity
    return {
        "dropout": {},  # amplitude-free by construction
        "saturation": {"limit": rail, "gain": 10.0},
        "clipping": {"limit": rail},
        "baseline_offset": {"offset": float(np.percentile(profile.rms, 50)) * severity},
        "noise_burst": {"amplitude": float(np.percentile(profile.rms, 50)) * severity},
    }


def calibrate(
    recordings: Iterable[EmgRecording],
    config: PreprocessConfig | None = None,
    margin: float = 3.0,
) -> dict[str, Any]:
    """Profile plus suggested thresholds plus the derivation, ready to record."""
    profile = profile_amplitudes(recordings, config)
    thresholds = suggest_qc_thresholds(profile, margin=margin)
    return {
        "profile": profile.summary(),
        "suggested_qc_kwargs": thresholds,
        "suggested_corruption_kwargs": suggest_corruption_kwargs(profile),
        "derivation": {
            "min_rms": "p0.1 of window RMS x 0.1",
            "flatline_std": "p0.1 of window RMS x 0.1",
            "max_rms": f"p99.9 of window RMS x {margin}",
            "max_offset": f"p99.9 of |window mean| x {margin}",
            "saturation_limit": f"p99.9 of window max|x| x {margin}",
        },
    }


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", help="dataset directory, e.g. data/ninapro_db6")
    parser.add_argument("--dataset", default="ninapro_db6", choices=["ninapro_db6"])
    parser.add_argument("--subjects", nargs="*", default=None)
    parser.add_argument("--sessions", nargs="*", default=None)
    parser.add_argument(
        "--channels",
        nargs="*",
        type=int,
        default=None,
        help="montage to profile. Calibrate on the channels you will gate on — "
        "pooling a weak electrode with strong ones produces thresholds that suit "
        "neither (see suggest_qc_thresholds).",
    )
    parser.add_argument("--margin", type=float, default=3.0)
    args = parser.parse_args(argv)

    from .loaders import NinaproDB6Loader

    # Passing channels=None explicitly means "keep all 16 columns", padding
    # included — not what an omitted flag should do.
    loader = (
        NinaproDB6Loader(args.root, channels=args.channels)
        if args.channels
        else NinaproDB6Loader(args.root)
    )
    result = calibrate(
        loader.load(subjects=args.subjects, sessions=args.sessions), margin=args.margin
    )
    result["dataset"] = args.dataset
    result["subjects"] = args.subjects or "all"
    result["channels"] = args.channels or "loader default"
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
