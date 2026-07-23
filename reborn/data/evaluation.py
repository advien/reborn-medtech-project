"""Metrics and the harness that runs a model across evaluation protocols.

Deliberately free of any modelling library. The caller supplies a `fit_predict`
callable, so the same harness serves LDA, logistic regression, or anything else,
and `reborn` keeps scikit-learn as an optional extra rather than a dependency.

On the direction of the import: this module reads
`reborn.decision.confidence_gate`. That is the offline research layer measuring
the runtime component, which is the point — a reimplemented gate would answer a
question about a system that does not exist. The prohibition runs the other way:
`decision/`, `safety/`, and `control/` must not import `reborn.data`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

import numpy as np

from ..decision.confidence_gate import ConfidenceGate
from .records import REST_LABEL
from .splits import Split

FitPredict = Callable[[np.ndarray, np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]
"""`(X_train, y_train, X_test) -> (predictions, confidence)`.

`confidence` is the model's probability for the *predicted* class, in [0, 1] —
the quantity `ConfidenceGate` consumes at runtime.
"""


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #


def accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.asarray(y_true) == np.asarray(y_pred)))


def balanced_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean per-class recall.

    The headline number for these datasets: DB6 windows are roughly a quarter
    rest, so plain accuracy rewards a model that leans toward the majority class.
    """
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    recalls = [
        float(np.mean(y_pred[y_true == label] == label))
        for label in np.unique(y_true)
        if np.any(y_true == label)
    ]
    return float(np.mean(recalls)) if recalls else 0.0


def expected_calibration_error(
    y_true: np.ndarray, y_pred: np.ndarray, confidence: np.ndarray, n_bins: int = 10
) -> float:
    """Weighted gap between confidence and accuracy across confidence bins.

    The phase-B quantity of interest is not this number on its own but how it
    moves between the within-session and cross-session protocols: a model that
    loses accuracy while holding its confidence is one that opens the gate on
    predictions it should not.
    """
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    confidence = np.asarray(confidence, dtype=float)
    correct = (y_true == y_pred).astype(float)

    edges = np.linspace(0.0, 1.0, n_bins + 1)
    error = 0.0
    for low, high in zip(edges[:-1], edges[1:]):
        # Half-open bins, closing the last one so confidence == 1.0 is counted.
        in_bin = (confidence > low) & (confidence <= high) if low > 0 else (confidence <= high)
        if not in_bin.any():
            continue
        weight = float(np.mean(in_bin))
        error += weight * abs(float(np.mean(correct[in_bin])) - float(np.mean(confidence[in_bin])))
    return error


def reliability_bins(
    y_true: np.ndarray, y_pred: np.ndarray, confidence: np.ndarray, n_bins: int = 10
) -> list[dict[str, float]]:
    """Per-bin confidence vs. accuracy — the reliability diagram, as data."""
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    confidence = np.asarray(confidence, dtype=float)
    correct = (y_true == y_pred).astype(float)

    edges = np.linspace(0.0, 1.0, n_bins + 1)
    rows: list[dict[str, float]] = []
    for low, high in zip(edges[:-1], edges[1:]):
        in_bin = (confidence > low) & (confidence <= high) if low > 0 else (confidence <= high)
        rows.append(
            {
                "bin_low": float(low),
                "bin_high": float(high),
                "n": int(np.sum(in_bin)),
                "mean_confidence": float(np.mean(confidence[in_bin])) if in_bin.any() else float("nan"),
                "accuracy": float(np.mean(correct[in_bin])) if in_bin.any() else float("nan"),
            }
        )
    return rows


def unsafe_assist_rate(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    confidence: np.ndarray,
    gate: ConfidenceGate | None = None,
    rest_label: int = REST_LABEL,
) -> float:
    """Fraction of windows where the gate would permit assist during true rest.

    This is the failure `docs/safety.md` calls the worst one — not "no assist",
    but assist the user did not ask for. Computed by running predictions through
    the real `ConfidenceGate`, so the number describes the deployed policy.

    A window counts as unsafe when the gate allows assist with a non-zero
    ceiling, the model predicts movement, and the truth is rest.
    """
    gate = gate or ConfidenceGate()
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    confidence = np.asarray(confidence, dtype=float)

    allowed = np.array([gate.evaluate(float(c)).assist_scale > 0.0 for c in confidence])
    return float(np.mean(allowed & (y_pred != rest_label) & (y_true == rest_label)))


def assist_availability(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    confidence: np.ndarray,
    gate: ConfidenceGate | None = None,
    rest_label: int = REST_LABEL,
) -> float:
    """Fraction of genuine movement windows the gate would actually assist.

    The counterweight to `unsafe_assist_rate`: a gate clamped shut is perfectly
    safe and perfectly useless. Reported together, the two trace the trade-off
    curve as the threshold sweeps.
    """
    gate = gate or ConfidenceGate()
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    confidence = np.asarray(confidence, dtype=float)

    movement = y_true != rest_label
    if not movement.any():
        return float("nan")
    allowed = np.array([gate.evaluate(float(c)).assist_scale > 0.0 for c in confidence])
    return float(np.mean((allowed & (y_pred != rest_label))[movement]))


# --------------------------------------------------------------------------- #
# Harness
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ProtocolResult:
    """One split, evaluated."""

    protocol: str
    split: str
    n_train: int
    n_test: int
    accuracy: float
    balanced_accuracy: float
    ece: float
    unsafe_assist_rate: float
    assist_availability: float
    meta: dict[str, Any] = field(default_factory=dict)

    def as_row(self) -> dict[str, Any]:
        """Flat dict for CSV, with split metadata folded in."""
        row = {
            "protocol": self.protocol,
            "split": self.split,
            "n_train": self.n_train,
            "n_test": self.n_test,
            "accuracy": self.accuracy,
            "balanced_accuracy": self.balanced_accuracy,
            "ece": self.ece,
            "unsafe_assist_rate": self.unsafe_assist_rate,
            "assist_availability": self.assist_availability,
        }
        for key, value in self.meta.items():
            row[f"meta_{key}"] = value if not isinstance(value, list) else ",".join(map(str, value))
        return row


def evaluate_split(
    X: np.ndarray,
    y: np.ndarray,
    split: Split,
    fit_predict: FitPredict,
    protocol: str = "",
    gate: ConfidenceGate | None = None,
) -> ProtocolResult:
    """Fit on the split's training rows, score its test rows."""
    X_train, y_train = X[split.train_index], y[split.train_index]
    X_test, y_test = X[split.test_index], y[split.test_index]

    y_pred, confidence = fit_predict(X_train, y_train, X_test)
    y_pred = np.asarray(y_pred)
    confidence = np.asarray(confidence, dtype=float)
    if y_pred.shape[0] != y_test.shape[0]:
        raise ValueError(f"fit_predict returned {y_pred.shape[0]} predictions for {y_test.shape[0]} rows")

    return ProtocolResult(
        protocol=protocol or split.name.split("/")[0],
        split=split.name,
        n_train=int(split.train_index.size),
        n_test=int(split.test_index.size),
        accuracy=accuracy(y_test, y_pred),
        balanced_accuracy=balanced_accuracy(y_test, y_pred),
        ece=expected_calibration_error(y_test, y_pred, confidence),
        unsafe_assist_rate=unsafe_assist_rate(y_test, y_pred, confidence, gate),
        assist_availability=assist_availability(y_test, y_pred, confidence, gate),
        meta=dict(split.meta),
    )


def evaluate_splits(
    X: np.ndarray,
    y: np.ndarray,
    splits: Iterable[Split],
    fit_predict: FitPredict,
    protocol: str = "",
    gate: ConfidenceGate | None = None,
    verbose: bool = False,
) -> list[ProtocolResult]:
    """`evaluate_split` over a protocol's splits."""
    results: list[ProtocolResult] = []
    for split in splits:
        result = evaluate_split(X, y, split, fit_predict, protocol, gate)
        results.append(result)
        if verbose:
            print(
                f"  {result.split:<44}acc {result.accuracy:.3f}  "
                f"bal {result.balanced_accuracy:.3f}  ece {result.ece:.3f}"
            )
    return results


def summarize(results: Sequence[ProtocolResult]) -> dict[str, float]:
    """Mean and spread across a protocol's splits.

    Reports the spread, not just the mean: under the cross-session protocol the
    variation between held-out sessions is the drift, and a mean alone hides it.
    """
    if not results:
        return {}
    fields = ("accuracy", "balanced_accuracy", "ece", "unsafe_assist_rate", "assist_availability")
    summary: dict[str, float] = {"n_splits": len(results)}
    for name in fields:
        values = np.array([getattr(r, name) for r in results], dtype=float)
        finite = values[np.isfinite(values)]
        summary[f"{name}_mean"] = float(np.mean(finite)) if finite.size else float("nan")
        summary[f"{name}_std"] = float(np.std(finite)) if finite.size else float("nan")
        summary[f"{name}_min"] = float(np.min(finite)) if finite.size else float("nan")
        summary[f"{name}_max"] = float(np.max(finite)) if finite.size else float("nan")
    return summary
