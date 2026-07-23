"""Tests for phase-B metrics and the evaluation harness.

`unsafe_assist_rate` gets the most attention here: it is the metric that carries
the safety claim, so it has to mean exactly what the paper will say it means.
"""

from __future__ import annotations

import numpy as np
import pytest

from reborn.data.evaluation import (
    ProtocolResult,
    accuracy,
    assist_availability,
    balanced_accuracy,
    evaluate_split,
    evaluate_splits,
    expected_calibration_error,
    reliability_bins,
    summarize,
    unsafe_assist_rate,
)
from reborn.data.splits import Split
from reborn.decision.confidence_gate import ConfidenceGate


def _perfect_fit_predict(confidence_value=1.0):
    def fit_predict(X_train, y_train, X_test):
        return np.zeros(len(X_test), dtype=int), np.full(len(X_test), confidence_value)

    return fit_predict


# --------------------------------------------------------------------------- #
# Basic metrics
# --------------------------------------------------------------------------- #


def test_accuracy():
    assert accuracy([0, 1, 1, 0], [0, 1, 0, 0]) == pytest.approx(0.75)


def test_balanced_accuracy_penalises_majority_class_bias():
    # 8 rest, 2 movement; predicting all rest gets 80% accuracy but 50% balanced.
    y_true = np.array([0] * 8 + [1] * 2)
    y_pred = np.zeros(10, dtype=int)

    assert accuracy(y_true, y_pred) == pytest.approx(0.8)
    assert balanced_accuracy(y_true, y_pred) == pytest.approx(0.5)


def test_balanced_accuracy_of_a_perfect_model_is_one():
    y = np.array([0, 1, 2, 0, 1, 2])
    assert balanced_accuracy(y, y) == pytest.approx(1.0)


# --------------------------------------------------------------------------- #
# Calibration
# --------------------------------------------------------------------------- #


def test_ece_is_zero_for_a_perfectly_calibrated_model():
    y_true = np.array([1] * 100)
    y_pred = np.array([1] * 100)
    assert expected_calibration_error(y_true, y_pred, np.ones(100)) == pytest.approx(0.0)


def test_ece_catches_confident_wrongness():
    """The failure mode phase B exists to measure: sure of itself, and wrong."""
    y_true = np.zeros(100, dtype=int)
    y_pred = np.ones(100, dtype=int)

    error = expected_calibration_error(y_true, y_pred, np.full(100, 0.95))

    assert error == pytest.approx(0.95, abs=0.01)


def test_ece_bins_cover_confidence_of_exactly_one():
    y = np.ones(10, dtype=int)
    rows = reliability_bins(y, y, np.ones(10))

    assert sum(row["n"] for row in rows) == 10


def test_reliability_bins_report_empty_bins_as_nan():
    y = np.ones(10, dtype=int)
    rows = reliability_bins(y, y, np.ones(10), n_bins=4)

    assert len(rows) == 4
    assert np.isnan(rows[0]["accuracy"])


# --------------------------------------------------------------------------- #
# The safety metric
# --------------------------------------------------------------------------- #


def test_unsafe_assist_counts_confident_movement_calls_during_rest():
    y_true = np.array([0, 0, 0, 1])          # three rest, one movement
    y_pred = np.array([1, 1, 0, 1])          # two false movement calls during rest
    confidence = np.array([0.9, 0.9, 0.9, 0.9])

    # Two of four windows are confident movement predictions on true rest.
    assert unsafe_assist_rate(y_true, y_pred, confidence) == pytest.approx(0.5)


def test_low_confidence_makes_a_wrong_prediction_safe():
    """The gate is the point: below threshold, a wrong call costs nothing."""
    y_true = np.zeros(4, dtype=int)
    y_pred = np.ones(4, dtype=int)

    confident = unsafe_assist_rate(y_true, y_pred, np.full(4, 0.9))
    unsure = unsafe_assist_rate(y_true, y_pred, np.full(4, 0.1))

    assert confident == pytest.approx(1.0)
    assert unsure == pytest.approx(0.0)


def test_unsafe_assist_uses_the_supplied_gate():
    y_true = np.zeros(4, dtype=int)
    y_pred = np.ones(4, dtype=int)
    confidence = np.full(4, 0.5)

    permissive = unsafe_assist_rate(y_true, y_pred, confidence, ConfidenceGate(0.1, 0.2))
    strict = unsafe_assist_rate(y_true, y_pred, confidence, ConfidenceGate(0.8, 0.9))

    assert permissive == pytest.approx(1.0)
    assert strict == pytest.approx(0.0)


def test_correct_rest_predictions_are_never_unsafe():
    y_true = np.zeros(4, dtype=int)
    y_pred = np.zeros(4, dtype=int)

    assert unsafe_assist_rate(y_true, y_pred, np.ones(4)) == pytest.approx(0.0)


def test_assist_availability_is_the_counterweight():
    """A gate clamped shut is perfectly safe and perfectly useless."""
    y_true = np.ones(4, dtype=int)
    y_pred = np.ones(4, dtype=int)
    confidence = np.full(4, 0.5)

    assert assist_availability(y_true, y_pred, confidence, ConfidenceGate(0.1, 0.2)) == pytest.approx(1.0)
    assert assist_availability(y_true, y_pred, confidence, ConfidenceGate(0.8, 0.9)) == pytest.approx(0.0)


def test_assist_availability_is_undefined_without_movement():
    y = np.zeros(4, dtype=int)
    assert np.isnan(assist_availability(y, y, np.ones(4)))


# --------------------------------------------------------------------------- #
# Harness
# --------------------------------------------------------------------------- #


def test_evaluate_split_scores_only_the_test_rows():
    X = np.arange(20).reshape(10, 2).astype(float)
    y = np.zeros(10, dtype=int)
    split = Split("p/a", train_index=np.arange(6), test_index=np.arange(6, 10))

    result = evaluate_split(X, y, split, _perfect_fit_predict(), protocol="demo")

    assert result.n_train == 6
    assert result.n_test == 4
    assert result.accuracy == pytest.approx(1.0)
    assert result.protocol == "demo"


def test_protocol_defaults_to_the_split_name_prefix():
    X = np.zeros((10, 2))
    y = np.zeros(10, dtype=int)
    split = Split("cross-session/s01/d02", train_index=np.arange(5), test_index=np.arange(5, 10))

    assert evaluate_split(X, y, split, _perfect_fit_predict()).protocol == "cross-session"


def test_mismatched_prediction_count_is_rejected():
    X = np.zeros((10, 2))
    y = np.zeros(10, dtype=int)
    split = Split("p/a", train_index=np.arange(5), test_index=np.arange(5, 10))

    def wrong(X_train, y_train, X_test):
        return np.zeros(3, dtype=int), np.ones(3)

    with pytest.raises(ValueError, match="3 predictions for 5 rows"):
        evaluate_split(X, y, split, wrong)


def test_evaluate_splits_returns_one_result_per_split():
    X = np.zeros((20, 2))
    y = np.zeros(20, dtype=int)
    splits = [
        Split("p/a", np.arange(0, 5), np.arange(5, 10)),
        Split("p/b", np.arange(10, 15), np.arange(15, 20)),
    ]

    results = evaluate_splits(X, y, splits, _perfect_fit_predict())

    assert [r.split for r in results] == ["p/a", "p/b"]


def test_result_row_folds_in_split_metadata():
    result = ProtocolResult(
        protocol="cross-session",
        split="cross-session/s01/d02",
        n_train=10,
        n_test=5,
        accuracy=0.8,
        balanced_accuracy=0.7,
        ece=0.1,
        unsafe_assist_rate=0.02,
        assist_availability=0.9,
        meta={"subject": "s01", "train_sessions": ["d01", "d02"]},
    )

    row = result.as_row()

    assert row["meta_subject"] == "s01"
    assert row["meta_train_sessions"] == "d01,d02"


def test_summarize_reports_spread_not_just_the_mean():
    """Between-session variation is the drift; a mean alone hides it."""
    results = [
        ProtocolResult("p", f"p/{i}", 10, 5, acc, acc, 0.1, 0.0, 1.0)
        for i, acc in enumerate([0.9, 0.5])
    ]

    summary = summarize(results)

    assert summary["accuracy_mean"] == pytest.approx(0.7)
    assert summary["accuracy_min"] == pytest.approx(0.5)
    assert summary["accuracy_max"] == pytest.approx(0.9)
    assert summary["accuracy_std"] > 0


def test_summarize_of_nothing_is_empty():
    assert summarize([]) == {}


def test_summarize_ignores_undefined_values():
    results = [
        ProtocolResult("p", "p/0", 10, 5, 0.8, 0.8, 0.1, 0.0, float("nan")),
        ProtocolResult("p", "p/1", 10, 5, 0.6, 0.6, 0.1, 0.0, 0.5),
    ]

    summary = summarize(results)

    assert summary["assist_availability_mean"] == pytest.approx(0.5)
