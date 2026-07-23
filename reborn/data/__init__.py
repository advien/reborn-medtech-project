"""Open-dataset loading and preprocessing for phase-B research.

Offline and research-side: `reborn.decision`, `reborn.safety`, and
`reborn.control` must not import this package — sensor data reaches them only
through the HAL. See `docs/research/phase-b-plan.md`.
"""

from .evaluation import (
    ProtocolResult,
    balanced_accuracy,
    evaluate_splits,
    expected_calibration_error,
    summarize,
    unsafe_assist_rate,
)
from .features import FEATURE_NAMES, feature_matrix, standardize
from .pipeline import PreprocessConfig, build_window_set, load_window_set, preprocess, save_window_set
from .records import EmgRecording, QcReport, WindowSet
from .splits import (
    Split,
    add_calibration,
    cross_session_splits,
    cross_subject_splits,
    random_window_split,
    within_session_splits,
)

__all__ = [
    "FEATURE_NAMES",
    "EmgRecording",
    "PreprocessConfig",
    "ProtocolResult",
    "QcReport",
    "Split",
    "WindowSet",
    "add_calibration",
    "balanced_accuracy",
    "build_window_set",
    "cross_session_splits",
    "cross_subject_splits",
    "evaluate_splits",
    "expected_calibration_error",
    "feature_matrix",
    "load_window_set",
    "preprocess",
    "random_window_split",
    "save_window_set",
    "standardize",
    "summarize",
    "unsafe_assist_rate",
    "within_session_splits",
]
