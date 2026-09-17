"""Tests for phase-B metrics and the evaluation harness.

The gated quantities get the most attention: they are the numbers that carry
the "when not to help" reading, so they have to mean exactly what the notebooks
say they mean — and they must never be computed against an implicit gate.
"""

from __future__ import annotations

import numpy as np
import pytest

from reborn.data.evaluation import (
    ProtocolResult,
    accuracy,
    assist_availability,
    balanced_accuracy,
    brier_score,
    coverage,
    evaluate_split,
    evaluate_splits,
    expected_calibration_error,
    false_assist_rate,
    log_loss,
    pool_reliability_bins,
    reliability_bins,
    selective_risk,
    summarize,
    unsafe_assist_rate,
)
from reborn.data.splits import Split
from reborn.decision.confidence_gate import ConfidenceGate


def _perfect_fit_predict(confidence_value=1.0):
    def fit_predict(X_train, y_train, X_test):
        return np.zeros(len(X_test), dtype=int), np.full(len(X_test), confidence_value)

    return fit_predict


def _result(**overrides) -> ProtocolResult:
    base = dict(
        protocol="p",
        split="p/0",
        n_train=10,
        n_test=5,
        accuracy=0.8,
        balanced_accuracy=0.8,
        ece=0.1,
        brier=0.1,
        nll=0.3,
        false_assist_rate=0.0,
    )
    base.update(overrides)
    return ProtocolResult(**base)


# --------------------------------------------------------------------------- #
# Discrimination
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


def test_pooling_reliability_bins_matches_bins_of_the_concatenation():
    rng = np.random.default_rng(0)
    parts = []
    for _ in range(3):
        y = rng.integers(0, 2, 50)
        pred = rng.integers(0, 2, 50)
        conf = rng.uniform(0.5, 1.0, 50)
        parts.append((y, pred, conf))

    pooled = pool_reliability_bins(reliability_bins(y, p, c, n_bins=5) for y, p, c in parts)
    direct = reliability_bins(
        np.concatenate([y for y, _, _ in parts]),
        np.concatenate([p for _, p, _ in parts]),
        np.concatenate([c for _, _, c in parts]),
        n_bins=5,
    )

    for a, b in zip(pooled, direct):
        assert a["n"] == b["n"]
        if a["n"]:
            assert a["mean_confidence"] == pytest.approx(b["mean_confidence"])
            assert a["accuracy"] == pytest.approx(b["accuracy"])


# --------------------------------------------------------------------------- #
# Proper scoring rules
# --------------------------------------------------------------------------- #


def test_binary_brier_of_a_perfect_model_is_zero_and_of_an_uninformative_one_is_a_quarter():
    y = np.array([0, 1, 1, 0])
    assert brier_score(y, np.array([0.0, 1.0, 1.0, 0.0])) == pytest.approx(0.0)
    assert brier_score(y, np.full(4, 0.5)) == pytest.approx(0.25)


def test_multiclass_brier_is_the_sum_form_and_twice_the_binary_form_for_two_classes():
    y = np.array([0, 1, 1, 0])
    p_pos = np.array([0.2, 0.9, 0.6, 0.4])
    two_column = np.column_stack([1 - p_pos, p_pos])

    assert brier_score(y, two_column, classes=[0, 1]) == pytest.approx(2 * brier_score(y, p_pos))


def test_multiclass_brier_respects_class_order():
    y = np.array([3, 9])
    proba = np.array([[1.0, 0.0], [0.0, 1.0]])
    assert brier_score(y, proba, classes=[3, 9]) == pytest.approx(0.0)
    assert brier_score(y, proba, classes=[9, 3]) == pytest.approx(2.0)


def test_brier_rejects_unknown_classes_and_bad_shapes():
    with pytest.raises(ValueError, match="absent"):
        brier_score(np.array([0, 5]), np.eye(2), classes=[0, 1])
    with pytest.raises(ValueError, match="proba must be"):
        brier_score(np.array([0, 1]), np.ones((3, 2)))


def test_log_loss_is_near_zero_when_right_and_large_when_confidently_wrong():
    y = np.array([1, 1, 0])
    assert log_loss(y, np.array([0.999, 0.999, 0.001])) < 0.01
    wrong = log_loss(y, np.array([0.001, 0.001, 0.999]))
    assert wrong > 5.0
    assert np.isfinite(wrong)  # clipped, never inf


def test_log_loss_binary_and_two_column_forms_agree():
    y = np.array([0, 1, 1, 0])
    p_pos = np.array([0.2, 0.9, 0.6, 0.4])
    two_column = np.column_stack([1 - p_pos, p_pos])
    assert log_loss(y, two_column, classes=[0, 1]) == pytest.approx(log_loss(y, p_pos))


def test_log_loss_multiclass_uses_the_true_class_column():
    y = np.array([3, 9])
    proba = np.array([[0.5, 0.5], [0.25, 0.75]])
    expected = -np.mean(np.log([0.5, 0.75]))
    assert log_loss(y, proba, classes=[3, 9]) == pytest.approx(expected)


# --------------------------------------------------------------------------- #
# Ungated assist quantity
# --------------------------------------------------------------------------- #


def test_false_assist_rate_counts_movement_calls_during_rest_over_all_windows():
    y_true = np.array([0, 0, 0, 1])
    y_pred = np.array([1, 1, 0, 1])
    assert false_assist_rate(y_true, y_pred) == pytest.approx(0.5)


def test_false_assist_rate_is_zero_for_correct_rest():
    y = np.zeros(4, dtype=int)
    assert false_assist_rate(y, y) == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
# Gated quantities — the gate is required
# --------------------------------------------------------------------------- #


def test_gated_metrics_have_no_default_gate():
    y = np.zeros(4, dtype=int)
    conf = np.full(4, 0.9)
    with pytest.raises(TypeError):
        unsafe_assist_rate(y, np.ones(4, dtype=int), conf)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        unsafe_assist_rate(y, np.ones(4, dtype=int), conf, None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        coverage(conf, None)  # type: ignore[arg-type]


def test_unsafe_assist_counts_confident_movement_calls_during_rest():
    y_true = np.array([0, 0, 0, 1])          # three rest, one movement
    y_pred = np.array([1, 1, 0, 1])          # two false movement calls during rest
    confidence = np.array([0.9, 0.9, 0.9, 0.9])

    gate = ConfidenceGate(0.4, 0.7)
    assert unsafe_assist_rate(y_true, y_pred, confidence, gate) == pytest.approx(0.5)


def test_low_confidence_makes_a_wrong_prediction_safe_under_the_gate():
    """The gate is the point: below threshold, a wrong call costs nothing."""
    y_true = np.zeros(4, dtype=int)
    y_pred = np.ones(4, dtype=int)
    gate = ConfidenceGate(0.4, 0.7)

    assert unsafe_assist_rate(y_true, y_pred, np.full(4, 0.9), gate) == pytest.approx(1.0)
    assert unsafe_assist_rate(y_true, y_pred, np.full(4, 0.1), gate) == pytest.approx(0.0)


def test_unsafe_assist_uses_the_supplied_gate():
    y_true = np.zeros(4, dtype=int)
    y_pred = np.ones(4, dtype=int)
    confidence = np.full(4, 0.5)

    permissive = unsafe_assist_rate(y_true, y_pred, confidence, ConfidenceGate(0.1, 0.2))
    strict = unsafe_assist_rate(y_true, y_pred, confidence, ConfidenceGate(0.8, 0.9))

    assert permissive == pytest.approx(1.0)
    assert strict == pytest.approx(0.0)


def test_a_binary_task_never_closes_a_gate_below_one_half():
    """The inert-gate trap: predicted-class probability is >= 0.5 on a binary task."""
    y_true = np.zeros(4, dtype=int)
    y_pred = np.ones(4, dtype=int)
    confidence = np.full(4, 0.5)  # the lowest a binary max-proba can be

    assert unsafe_assist_rate(y_true, y_pred, confidence, ConfidenceGate(0.4, 0.7)) == pytest.approx(1.0)
    assert unsafe_assist_rate(y_true, y_pred, confidence, ConfidenceGate(0.6, 0.6)) == pytest.approx(0.0)


def test_correct_rest_predictions_are_never_unsafe():
    y = np.zeros(4, dtype=int)
    assert unsafe_assist_rate(y, y, np.ones(4), ConfidenceGate(0.4, 0.7)) == pytest.approx(0.0)


def test_assist_availability_is_the_counterweight():
    """A gate clamped shut is perfectly safe and perfectly useless."""
    y_true = np.ones(4, dtype=int)
    y_pred = np.ones(4, dtype=int)
    confidence = np.full(4, 0.5)

    assert assist_availability(y_true, y_pred, confidence, ConfidenceGate(0.1, 0.2)) == pytest.approx(1.0)
    assert assist_availability(y_true, y_pred, confidence, ConfidenceGate(0.8, 0.9)) == pytest.approx(0.0)


def test_assist_availability_is_undefined_without_movement():
    y = np.zeros(4, dtype=int)
    assert np.isnan(assist_availability(y, y, np.ones(4), ConfidenceGate(0.4, 0.7)))


def test_coverage_and_selective_risk_form_the_risk_coverage_pair():
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 1, 1, 0])          # windows 1 and 3 are wrong
    confidence = np.array([0.95, 0.95, 0.6, 0.6])

    open_gate = ConfidenceGate(0.5, 0.5)
    assert coverage(confidence, open_gate) == pytest.approx(1.0)
    assert selective_risk(y_true, y_pred, confidence, open_gate) == pytest.approx(0.5)

    strict = ConfidenceGate(0.9, 0.9)         # admits only the two confident windows
    assert coverage(confidence, strict) == pytest.approx(0.5)
    assert selective_risk(y_true, y_pred, confidence, strict) == pytest.approx(0.5)

    shut = ConfidenceGate(0.99, 0.99)
    assert coverage(confidence, shut) == pytest.approx(0.0)
    assert np.isnan(selective_risk(y_true, y_pred, confidence, shut))


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
    assert np.isnan(result.brier) and np.isnan(result.nll)  # no proba supplied
    assert sum(b["n"] for b in result.reliability) == 4


def test_evaluate_split_scores_probabilities_when_supplied():
    X = np.zeros((10, 2))
    y = np.array([0, 1] * 5)
    split = Split("p/a", train_index=np.arange(6), test_index=np.arange(6, 10))

    def fit_predict(X_train, y_train, X_test):
        p_pos = np.array([0.1, 0.9, 0.2, 0.8])
        return (p_pos > 0.5).astype(int), np.maximum(p_pos, 1 - p_pos), np.column_stack([1 - p_pos, p_pos])

    result = evaluate_split(X, y, split, fit_predict)

    assert result.brier == pytest.approx(brier_score(y[6:10], np.array([0.1, 0.9, 0.2, 0.8])))
    assert result.nll == pytest.approx(log_loss(y[6:10], np.array([0.1, 0.9, 0.2, 0.8])))


def test_evaluate_split_rejects_a_probability_matrix_of_the_wrong_shape():
    X = np.zeros((10, 2))
    y = np.array([0, 1] * 5)
    split = Split("p/a", train_index=np.arange(6), test_index=np.arange(6, 10))

    def fit_predict(X_train, y_train, X_test):
        return np.zeros(4, dtype=int), np.ones(4), np.ones((4, 3))

    with pytest.raises(ValueError, match="proba must be"):
        evaluate_split(X, y, split, fit_predict)


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


def test_result_row_folds_in_split_metadata_and_excludes_bins():
    result = _result(
        protocol="cross-session",
        split="cross-session/s01/d02",
        meta={"subject": "s01", "train_sessions": ["d01", "d02"]},
        reliability=[{"bin_low": 0.0, "bin_high": 1.0, "n": 5, "mean_confidence": 0.9, "accuracy": 0.8}],
    )

    row = result.as_row()

    assert row["meta_subject"] == "s01"
    assert row["meta_train_sessions"] == "d01,d02"
    assert "reliability" not in row
    assert "unsafe_assist_rate" not in row  # gated quantities are not harness output


def test_summarize_reports_spread_not_just_the_mean():
    """Between-session variation matters; a mean alone hides it."""
    results = [_result(split=f"p/{i}", accuracy=acc, balanced_accuracy=acc) for i, acc in enumerate([0.9, 0.5])]

    summary = summarize(results)

    assert summary["accuracy_mean"] == pytest.approx(0.7)
    assert summary["accuracy_min"] == pytest.approx(0.5)
    assert summary["accuracy_max"] == pytest.approx(0.9)
    assert summary["accuracy_std"] > 0
    assert "brier_mean" in summary and "nll_mean" in summary


def test_summarize_of_nothing_is_empty():
    assert summarize([]) == {}


def test_summarize_ignores_undefined_values():
    results = [_result(split="p/0", brier=float("nan")), _result(split="p/1", brier=0.5)]

    summary = summarize(results)

    assert summary["brier_mean"] == pytest.approx(0.5)
