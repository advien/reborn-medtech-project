"""Metrics and the harness that runs a model across evaluation protocols.

Deliberately free of any modelling library. The caller supplies a `fit_predict`
callable, so the same harness serves LDA, logistic regression, or anything else,
and `reborn` keeps scikit-learn as an optional extra rather than a dependency.

On the direction of the import: this module reads
`reborn.decision.confidence_gate`. That is the offline research layer measuring
the runtime component, which is the point — a reimplemented gate would answer a
question about a system that does not exist. The prohibition runs the other way:
`decision/`, `safety/`, and `control/` must not import `reborn.data`.

Two families of metric live here and must not be confused:

* **Ungated** quantities (`accuracy`, `balanced_accuracy`, the probability-quality
  scores, `false_assist_rate`) describe the classifier alone. The harness
  (`evaluate_split`) reports only these.
* **Gated** quantities (`unsafe_assist_rate`, `assist_availability`, `coverage`,
  `selective_risk`) describe classifier *plus* a `ConfidenceGate` and take the
  gate as a required argument. There is no default gate: on a binary task the
  predicted-class probability is never below 0.5, so a default gate with
  `low_threshold=0.4` would never close and the number would carry a safety
  meaning it does not have.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

import numpy as np

from ..decision.confidence_gate import ConfidenceGate
from .records import REST_LABEL
from .splits import Split

FitPredict = Callable[[np.ndarray, np.ndarray, np.ndarray], tuple]
"""`(X_train, y_train, X_test) -> (predictions, confidence[, proba])`.

`confidence` is the model's probability for the *predicted* class, in [0, 1] —
the quantity `ConfidenceGate` consumes at runtime.

`proba`, when returned, is the full `(n_test, n_classes)` probability matrix
with columns ordered as `np.unique(y_train)` (scikit-learn's `classes_`
convention). It is what the proper scoring rules need; without it `brier` and
`nll` are reported as NaN.
"""


# --------------------------------------------------------------------------- #
# Discrimination
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


# --------------------------------------------------------------------------- #
# Probability quality
# --------------------------------------------------------------------------- #


def expected_calibration_error(
    y_true: np.ndarray, y_pred: np.ndarray, confidence: np.ndarray, n_bins: int = 10
) -> float:
    """Weighted gap between confidence and accuracy across confidence bins.

    A calibration metric only: it says nothing about sharpness, and it depends
    on the binning. Report it beside a proper scoring rule (`brier_score`,
    `log_loss`), never alone.
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


def pool_reliability_bins(bin_sets: Iterable[Sequence[dict[str, float]]]) -> list[dict[str, float]]:
    """Merge per-split `reliability_bins` output into one diagram, exactly.

    Each bin's mean confidence and accuracy are count-weighted, so pooling the
    per-split tables gives the same numbers as computing the bins on the
    concatenated predictions.
    """
    pooled: dict[int, dict[str, float]] = {}
    for bins in bin_sets:
        for i, row in enumerate(bins):
            acc = pooled.setdefault(
                i,
                {"bin_low": row["bin_low"], "bin_high": row["bin_high"], "n": 0, "_conf": 0.0, "_acc": 0.0},
            )
            if row["n"]:
                acc["n"] += int(row["n"])
                acc["_conf"] += float(row["mean_confidence"]) * row["n"]
                acc["_acc"] += float(row["accuracy"]) * row["n"]
    out: list[dict[str, float]] = []
    for i in sorted(pooled):
        row = pooled[i]
        n = row["n"]
        out.append(
            {
                "bin_low": row["bin_low"],
                "bin_high": row["bin_high"],
                "n": int(n),
                "mean_confidence": row["_conf"] / n if n else float("nan"),
                "accuracy": row["_acc"] / n if n else float("nan"),
            }
        )
    return out


def _one_hot(y_true: np.ndarray, classes: np.ndarray) -> np.ndarray:
    classes = np.asarray(classes)
    positions = {label: k for k, label in enumerate(classes.tolist())}
    missing = set(np.unique(y_true).tolist()) - set(positions)
    if missing:
        raise ValueError(f"y_true contains classes {sorted(missing)} absent from `classes`")
    onehot = np.zeros((len(y_true), len(classes)))
    onehot[np.arange(len(y_true)), [positions[v] for v in np.asarray(y_true).tolist()]] = 1.0
    return onehot


def brier_score(y_true: np.ndarray, proba: np.ndarray, classes: Sequence[Any] | None = None) -> float:
    """Brier score — a proper scoring rule, lower is better.

    Two forms, and they are **not on the same scale**:

    * `proba` 1-D: the probability of the positive class (`classes[-1]`, or
      label 1 when `classes` is omitted). Returns the one-column binary Brier
      score, `mean((p - y)^2)`, in [0, 1]; an uninformative p = 0.5 scores 0.25.
    * `proba` 2-D `(n, K)`: the multiclass form `mean(sum_k (p_k - y_k)^2)`, in
      [0, 2]. For K = 2 this is exactly twice the one-column form.

    A proper scoring rule rewards both calibration and sharpness together; it is
    not a pure calibration measure and should not be read as one.
    """
    y_true = np.asarray(y_true)
    proba = np.asarray(proba, dtype=float)
    if proba.ndim == 1:
        positive = classes[-1] if classes is not None else 1
        target = (y_true == positive).astype(float)
        return float(np.mean((proba - target) ** 2))
    if proba.ndim != 2 or proba.shape[0] != y_true.shape[0]:
        raise ValueError(f"proba must be (n,) or (n, K) with n = {y_true.shape[0]}, got {proba.shape}")
    classes = np.arange(proba.shape[1]) if classes is None else np.asarray(classes)
    return float(np.mean(np.sum((proba - _one_hot(y_true, classes)) ** 2, axis=1)))


def log_loss(
    y_true: np.ndarray, proba: np.ndarray, classes: Sequence[Any] | None = None, eps: float = 1e-15
) -> float:
    """Negative log-likelihood (NLL) of the true class — a proper scoring rule.

    `proba` 1-D is the positive-class probability (binary); 2-D is the full
    `(n, K)` matrix with columns in `classes` order. Probabilities are clipped
    to `[eps, 1 - eps]` so a confident wrong call is penalised heavily but
    finitely. Unlike Brier, the two forms are on the same scale.
    """
    y_true = np.asarray(y_true)
    proba = np.asarray(proba, dtype=float)
    if proba.ndim == 1:
        positive = classes[-1] if classes is not None else 1
        target = (y_true == positive).astype(float)
        p = np.clip(proba, eps, 1.0 - eps)
        return float(-np.mean(target * np.log(p) + (1.0 - target) * np.log(1.0 - p)))
    if proba.ndim != 2 or proba.shape[0] != y_true.shape[0]:
        raise ValueError(f"proba must be (n,) or (n, K) with n = {y_true.shape[0]}, got {proba.shape}")
    classes = np.arange(proba.shape[1]) if classes is None else np.asarray(classes)
    p_true = np.sum(np.clip(proba, eps, 1.0) * _one_hot(y_true, classes), axis=1)
    return float(-np.mean(np.log(p_true)))


# --------------------------------------------------------------------------- #
# Assist-related quantities — ungated
# --------------------------------------------------------------------------- #


def false_assist_rate(y_true: np.ndarray, y_pred: np.ndarray, rest_label: int = REST_LABEL) -> float:
    """Fraction of **all** windows where the model calls movement during true rest.

    Ungated: this is the classifier's own false-movement rate with no confidence
    threshold applied, and it must not be read as a safety quantity. Denominator
    is every test window (not only rest windows), so it is comparable across
    splits with different class balance only together with the rest share.
    """
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    return float(np.mean((y_pred != rest_label) & (y_true == rest_label)))


# --------------------------------------------------------------------------- #
# Assist-related quantities — gated (gate is required, never defaulted)
# --------------------------------------------------------------------------- #


def _allowed(confidence: np.ndarray, gate: ConfidenceGate) -> np.ndarray:
    if gate is None:
        raise TypeError("a ConfidenceGate is required — there is no default gate for gated metrics")
    return np.array([gate.evaluate(float(c)).assist_scale > 0.0 for c in np.asarray(confidence, dtype=float)])


def unsafe_assist_rate(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    confidence: np.ndarray,
    gate: ConfidenceGate,
    rest_label: int = REST_LABEL,
) -> float:
    """Fraction of **all** windows where the gate would permit assist during true rest.

    This is the failure `docs/safety.md` calls the worst one — not "no assist",
    but assist the user did not ask for. Computed by running predictions through
    the real `ConfidenceGate`, so the number describes classifier + gate at the
    supplied thresholds, and nothing else.

    A window counts as unsafe when the gate allows assist with a non-zero
    ceiling, the model predicts movement, and the truth is rest. Denominator:
    every test window.
    """
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    allowed = _allowed(confidence, gate)
    return float(np.mean(allowed & (y_pred != rest_label) & (y_true == rest_label)))


def assist_availability(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    confidence: np.ndarray,
    gate: ConfidenceGate,
    rest_label: int = REST_LABEL,
) -> float:
    """Fraction of **genuine movement** windows the gate would actually assist.

    The counterweight to `unsafe_assist_rate`: a gate clamped shut is perfectly
    safe and perfectly useless. Denominator: true-movement windows only — a
    different denominator from `unsafe_assist_rate`, so the two do not form a
    risk–coverage pair; see `coverage` / `selective_risk` for that.
    """
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    movement = y_true != rest_label
    if not movement.any():
        return float("nan")
    allowed = _allowed(confidence, gate)
    return float(np.mean((allowed & (y_pred != rest_label))[movement]))


def coverage(confidence: np.ndarray, gate: ConfidenceGate) -> float:
    """Fraction of **all** windows on which the gate lets the model act at all.

    Selective-prediction coverage: `1 - coverage` is the abstention rate.
    """
    return float(np.mean(_allowed(confidence, gate)))


def selective_risk(
    y_true: np.ndarray, y_pred: np.ndarray, confidence: np.ndarray, gate: ConfidenceGate
) -> float:
    """Error rate among the windows the gate lets through.

    Selective-prediction risk: the classifier's error conditioned on acting.
    NaN when the gate admits nothing. Together with `coverage` this is the
    standard risk–coverage pair.
    """
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    allowed = _allowed(confidence, gate)
    if not allowed.any():
        return float("nan")
    return float(np.mean((y_true != y_pred)[allowed]))


# --------------------------------------------------------------------------- #
# Harness
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ProtocolResult:
    """One split, evaluated — ungated quantities only.

    `brier` is the one-column binary form when the task has two classes and the
    multiclass sum-form otherwise (see `brier_score`); the two are not on one
    scale, so never compare a binary and a multiclass Brier directly. `nll` has
    one definition for both. Both are NaN when `fit_predict` returned no
    probability matrix.
    """

    protocol: str
    split: str
    n_train: int
    n_test: int
    accuracy: float
    balanced_accuracy: float
    ece: float
    brier: float
    nll: float
    false_assist_rate: float
    meta: dict[str, Any] = field(default_factory=dict)
    reliability: list[dict[str, float]] = field(default_factory=list, compare=False)

    def as_row(self) -> dict[str, Any]:
        """Flat dict for CSV, with split metadata folded in (bins excluded)."""
        row = {
            "protocol": self.protocol,
            "split": self.split,
            "n_train": self.n_train,
            "n_test": self.n_test,
            "accuracy": self.accuracy,
            "balanced_accuracy": self.balanced_accuracy,
            "ece": self.ece,
            "brier": self.brier,
            "nll": self.nll,
            "false_assist_rate": self.false_assist_rate,
        }
        for key, value in self.meta.items():
            row[f"meta_{key}"] = value if not isinstance(value, list) else ",".join(map(str, value))
        return row


SUMMARY_FIELDS = ("accuracy", "balanced_accuracy", "ece", "brier", "nll", "false_assist_rate")


def evaluate_split(
    X: np.ndarray,
    y: np.ndarray,
    split: Split,
    fit_predict: FitPredict,
    protocol: str = "",
    n_bins: int = 10,
) -> ProtocolResult:
    """Fit on the split's training rows, score its test rows."""
    X_train, y_train = X[split.train_index], y[split.train_index]
    X_test, y_test = X[split.test_index], y[split.test_index]

    out = fit_predict(X_train, y_train, X_test)
    y_pred = np.asarray(out[0])
    confidence = np.asarray(out[1], dtype=float)
    proba = np.asarray(out[2], dtype=float) if len(out) > 2 and out[2] is not None else None
    if y_pred.shape[0] != y_test.shape[0]:
        raise ValueError(f"fit_predict returned {y_pred.shape[0]} predictions for {y_test.shape[0]} rows")

    brier = nll = float("nan")
    if proba is not None:
        classes = np.unique(y_train)
        if proba.shape != (y_test.shape[0], classes.size):
            raise ValueError(
                f"proba must be ({y_test.shape[0]}, {classes.size}) in np.unique(y_train) order, got {proba.shape}"
            )
        if classes.size == 2:
            brier = brier_score(y_test, proba[:, 1], classes)
            nll = log_loss(y_test, proba[:, 1], classes)
        else:
            brier = brier_score(y_test, proba, classes)
            nll = log_loss(y_test, proba, classes)

    return ProtocolResult(
        protocol=protocol or split.name.split("/")[0],
        split=split.name,
        n_train=int(split.train_index.size),
        n_test=int(split.test_index.size),
        accuracy=accuracy(y_test, y_pred),
        balanced_accuracy=balanced_accuracy(y_test, y_pred),
        ece=expected_calibration_error(y_test, y_pred, confidence, n_bins),
        brier=brier,
        nll=nll,
        false_assist_rate=false_assist_rate(y_test, y_pred),
        meta=dict(split.meta),
        reliability=reliability_bins(y_test, y_pred, confidence, n_bins),
    )


def evaluate_splits(
    X: np.ndarray,
    y: np.ndarray,
    splits: Iterable[Split],
    fit_predict: FitPredict,
    protocol: str = "",
    verbose: bool = False,
) -> list[ProtocolResult]:
    """`evaluate_split` over a protocol's splits."""
    results: list[ProtocolResult] = []
    for split in splits:
        result = evaluate_split(X, y, split, fit_predict, protocol)
        results.append(result)
        if verbose:
            print(
                f"  {result.split:<44}acc {result.accuracy:.3f}  "
                f"bal {result.balanced_accuracy:.3f}  ece {result.ece:.3f}"
            )
    return results


def summarize(results: Sequence[ProtocolResult]) -> dict[str, float]:
    """Mean and spread across a protocol's splits.

    Reports the spread, not just the mean. Whether that spread is independent
    replication depends on the protocol — cross-session splits that share a
    training session are not — and the caller must say which.
    """
    if not results:
        return {}
    summary: dict[str, float] = {"n_splits": len(results)}
    for name in SUMMARY_FIELDS:
        values = np.array([getattr(r, name) for r in results], dtype=float)
        finite = values[np.isfinite(values)]
        summary[f"{name}_mean"] = float(np.mean(finite)) if finite.size else float("nan")
        summary[f"{name}_std"] = float(np.std(finite)) if finite.size else float("nan")
        summary[f"{name}_min"] = float(np.min(finite)) if finite.size else float("nan")
        summary[f"{name}_max"] = float(np.max(finite)) if finite.size else float("nan")
    return summary
