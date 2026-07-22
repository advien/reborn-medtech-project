"""Preprocessing, windowing, and the QC gate for open EMG datasets.

The governing rule (`docs/research/phase-b-plan.md` §5): **this module calls
`reborn.sensing`, it does not reimplement it.** Filtering and signal-quality
decisions here go through the same code the runtime loop uses, so what the paper
measures is what the system actually does. A notebook that band-passes its own
way is measuring a system that does not exist.

Order matters and is fixed: resample -> filter -> window -> QC gate -> features.
The QC gate runs *before* any model sees a window, because that is the order at
runtime: `reborn.sensing.emg_qc` decides whether EMG is trustworthy, and only
then does anything downstream act on it.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
from scipy import signal as _sig

from reborn.sensing.emg_qc import assess_quality_report
from reborn.sensing.filters import bandpass_filter, notch_filter

from .records import EmgRecording, QcReport, WindowSet


@dataclass(frozen=True)
class PreprocessConfig:
    """Every knob that affects what the model sees.

    Hashed into `fingerprint()` and written next to the cached windows, so a
    figure in the paper names the exact configuration that produced it.

    Args:
        target_sample_rate: common rate all datasets are resampled to. Native
            rates span 200 Hz (Myo) to 5120 Hz (putEMG); feature statistics are
            only comparable across datasets at a common rate.
        bandpass_hz: standard EMG band. `None` skips band-pass.
        notch_hz: mains frequency. `None` skips the notch.
        window_ms / stride_ms: analysis window and hop.
        pure_windows: keep only windows whose label is constant throughout.
            Mixed windows sit on a gesture transition and their label is
            arbitrary; with 200 ms windows against multi-second gestures the
            cost of dropping them is small and the label noise avoided is not.
        qc_channels: channel indices the quality gate inspects. `None` means all,
            which is both slow and unfaithful for these datasets — Reborn's own
            hardware has one or two channels, so gating on 14 forearm electrodes
            models a system that does not exist. Pick the subset that mirrors the
            target montage.
        qc_powerline: enable the mains-interference check. Off by default: it
            runs a Welch PSD per window per channel and dominates runtime on a
            full dataset. Enable it for the deliberately small QC audit in
            notebook 01.
        qc_kwargs: passed through to `assess_quality_report`. The amplitude and
            saturation thresholds are **absolute** and therefore scale-dependent;
            each dataset's units differ, so these must be set per dataset rather
            than inherited. Leaving the defaults on data in unfamiliar units
            produces a rejection rate that means nothing.
    """

    target_sample_rate: float = 1000.0
    bandpass_hz: tuple[float, float] | None = (20.0, 450.0)
    notch_hz: float | None = 50.0
    window_ms: float = 200.0
    stride_ms: float = 50.0
    pure_windows: bool = True
    qc_channels: tuple[int, ...] | None = None
    qc_powerline: bool = False
    qc_kwargs: dict[str, Any] = field(default_factory=dict)

    @property
    def window_samples(self) -> int:
        return max(1, int(round(self.window_ms * self.target_sample_rate / 1000.0)))

    @property
    def stride_samples(self) -> int:
        return max(1, int(round(self.stride_ms * self.target_sample_rate / 1000.0)))

    def fingerprint(self) -> str:
        """Short stable hash of the configuration, for the cache manifest."""
        blob = json.dumps(asdict(self), sort_keys=True, default=str)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# Resampling and filtering
# --------------------------------------------------------------------------- #


def resample_recording(recording: EmgRecording, target_rate: float) -> EmgRecording:
    """Polyphase resample to `target_rate`; labels are re-indexed, never interpolated."""
    if abs(recording.sample_rate - target_rate) < 1e-9:
        return recording
    ratio = Fraction(target_rate / recording.sample_rate).limit_denominator(1000)
    resampled = _sig.resample_poly(recording.signal, ratio.numerator, ratio.denominator, axis=0)

    # Labels are categorical: map each new sample to the nearest original one.
    n_new = resampled.shape[0]
    source_index = np.minimum(
        (np.arange(n_new) * recording.n_samples / n_new).astype(int), recording.n_samples - 1
    )
    return recording.with_signal(resampled, target_rate, recording.labels[source_index])


def filter_recording(recording: EmgRecording, config: PreprocessConfig) -> EmgRecording:
    """Band-pass and notch every channel, via `reborn.sensing.filters`."""
    out = recording.signal
    if config.bandpass_hz is not None:
        low, high = config.bandpass_hz
        nyquist = 0.5 * recording.sample_rate
        if high >= nyquist:
            raise ValueError(
                f"band-pass upper edge {high} Hz is at or above Nyquist ({nyquist} Hz) for "
                f"{recording.sample_rate} Hz data — lower it or raise target_sample_rate"
            )
        out = np.column_stack(
            [bandpass_filter(out[:, c], recording.sample_rate, low, high) for c in range(out.shape[1])]
        )
    if config.notch_hz is not None:
        out = np.column_stack(
            [notch_filter(out[:, c], recording.sample_rate, config.notch_hz) for c in range(out.shape[1])]
        )
    return recording.with_signal(out, recording.sample_rate, recording.labels)


def preprocess(recording: EmgRecording, config: PreprocessConfig) -> EmgRecording:
    """Resample then filter. Windowing is separate — see `window_recording`."""
    return filter_recording(resample_recording(recording, config.target_sample_rate), config)


# --------------------------------------------------------------------------- #
# Windowing
# --------------------------------------------------------------------------- #


def window_recording(
    recording: EmgRecording, config: PreprocessConfig
) -> tuple[np.ndarray, np.ndarray, QcReport]:
    """Slice a preprocessed recording into QC-gated windows.

    Each window is labelled by the label at its **last sample**, so the window is
    causal: it contains nothing from after the instant the decision would be
    made. Labelling by the majority or centre sample leaks future information and
    is a common source of inflated cross-session numbers.

    Returns `(windows, labels, qc)` where windows has shape
    `(n_kept, window_samples, n_channels)`.
    """
    width = config.window_samples
    stride = config.stride_samples
    if recording.n_samples < width:
        return (
            np.empty((0, width, recording.n_channels)),
            np.empty((0,), dtype=recording.labels.dtype),
            QcReport(total=0, kept=0),
        )

    starts = np.arange(0, recording.n_samples - width + 1, stride)
    channels = _qc_channels(config, recording.n_channels)
    qc_rate = recording.sample_rate if config.qc_powerline else None

    kept_windows: list[np.ndarray] = []
    kept_labels: list[Any] = []
    reasons: dict[str, int] = {}
    total = 0

    for start in starts:
        stop = start + width
        label_slice = recording.labels[start:stop]
        if config.pure_windows and not np.all(label_slice == label_slice[-1]):
            continue  # transition window — excluded before QC, it is a labelling
            # decision rather than a signal-quality one, and counting it as a QC
            # rejection would corrupt the reported rejection rate.
        total += 1

        window = recording.signal[start:stop]
        failures = _window_failures(window, channels, qc_rate, config.qc_kwargs)
        if failures:
            for reason in failures:
                reasons[reason] = reasons.get(reason, 0) + 1
            continue

        kept_windows.append(window)
        kept_labels.append(label_slice[-1])

    if kept_windows:
        windows = np.stack(kept_windows)
        labels = np.asarray(kept_labels)
    else:
        windows = np.empty((0, width, recording.n_channels))
        labels = np.empty((0,), dtype=recording.labels.dtype)

    return windows, labels, QcReport(total=total, kept=len(kept_windows), rejected_by_reason=reasons)


def build_window_set(
    recordings: Iterable[EmgRecording], config: PreprocessConfig, *, preprocessed: bool = False
) -> WindowSet:
    """Preprocess and window a collection of recordings into one `WindowSet`.

    Set `preprocessed=True` if the recordings already went through `preprocess`.
    """
    all_windows: list[np.ndarray] = []
    all_labels: list[np.ndarray] = []
    subjects: list[str] = []
    sessions: list[str] = []
    qc = QcReport(total=0, kept=0)
    sources: set[str] = set()

    for recording in recordings:
        prepared = recording if preprocessed else preprocess(recording, config)
        windows, labels, report = window_recording(prepared, config)
        qc = qc.merge(report)
        sources.add(prepared.source)
        if windows.shape[0] == 0:
            continue
        all_windows.append(windows)
        all_labels.append(labels)
        subjects.extend([prepared.subject_id] * windows.shape[0])
        sessions.extend([prepared.session_id] * windows.shape[0])

    if not all_windows:
        raise ValueError(
            "no windows survived preprocessing — check qc_kwargs thresholds against this "
            "dataset's amplitude units (see PreprocessConfig.qc_kwargs)"
        )

    return WindowSet(
        windows=np.concatenate(all_windows, axis=0),
        labels=np.concatenate(all_labels, axis=0),
        subject_ids=np.asarray(subjects, dtype=object),
        session_ids=np.asarray(sessions, dtype=object),
        sample_rate=config.target_sample_rate,
        qc=qc,
        source=",".join(sorted(s for s in sources if s)),
        meta={
            "config_fingerprint": config.fingerprint(),
            # Kept so the split protocols can derive how many neighbouring windows
            # overlap, and guard against leaking them across a train/test boundary.
            "window_samples": config.window_samples,
            "stride_samples": config.stride_samples,
        },
    )


# --------------------------------------------------------------------------- #
# Cache — the traceability contract
# --------------------------------------------------------------------------- #


def save_window_set(window_set: WindowSet, path: str | Path, config: PreprocessConfig) -> Path:
    """Write windows to `path` (.npz) plus a sibling `.manifest.json`.

    The manifest records the full configuration and its fingerprint so a result
    can be traced back to the exact preprocessing that produced it — the same
    contract phase A makes for its search log.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        windows=window_set.windows,
        labels=window_set.labels,
        subject_ids=window_set.subject_ids.astype(str),
        session_ids=window_set.session_ids.astype(str),
    )
    manifest = {
        "config": asdict(config),
        "config_fingerprint": config.fingerprint(),
        "source": window_set.source,
        "sample_rate": window_set.sample_rate,
        "n_windows": window_set.n_windows,
        "qc": {
            "total": window_set.qc.total,
            "kept": window_set.qc.kept,
            "rejection_rate": window_set.qc.rejection_rate,
            "rejected_by_reason": window_set.qc.rejected_by_reason,
        },
    }
    path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    return path


def load_window_set(path: str | Path) -> WindowSet:
    """Read back a cached `WindowSet` and its manifest."""
    path = Path(path)
    data = np.load(path, allow_pickle=False)
    manifest = json.loads(path.with_suffix(".manifest.json").read_text())
    qc_meta = manifest["qc"]
    return WindowSet(
        windows=data["windows"],
        labels=data["labels"],
        subject_ids=data["subject_ids"].astype(object),
        session_ids=data["session_ids"].astype(object),
        sample_rate=float(manifest["sample_rate"]),
        qc=QcReport(
            total=qc_meta["total"],
            kept=qc_meta["kept"],
            rejected_by_reason=qc_meta["rejected_by_reason"],
        ),
        source=manifest.get("source", ""),
        meta={
            "config_fingerprint": manifest["config_fingerprint"],
            "window_samples": manifest["config"]["window_ms"]
            * manifest["config"]["target_sample_rate"]
            / 1000.0,
            "stride_samples": manifest["config"]["stride_ms"]
            * manifest["config"]["target_sample_rate"]
            / 1000.0,
        },
    )


# --------------------------------------------------------------------------- #
# Internals
# --------------------------------------------------------------------------- #


def _qc_channels(config: PreprocessConfig, n_channels: int) -> Sequence[int]:
    if config.qc_channels is None:
        return range(n_channels)
    for c in config.qc_channels:
        if not 0 <= c < n_channels:
            raise ValueError(f"qc_channels index {c} out of range for {n_channels} channels")
    return config.qc_channels


def _window_failures(
    window: np.ndarray, channels: Sequence[int], qc_rate: float | None, qc_kwargs: dict[str, Any]
) -> tuple[str, ...]:
    """Failure reasons across the inspected channels.

    A window is rejected if *any* inspected channel fails. That is the
    conservative reading, and it is the one the invariant requires: uncertainty
    reduces autonomy, so a doubtful channel makes the whole frame doubtful.
    """
    failures: list[str] = []
    for c in channels:
        report = assess_quality_report(window[:, c], sample_rate=qc_rate, **qc_kwargs)
        failures.extend(report.failures)
    return tuple(dict.fromkeys(failures))
