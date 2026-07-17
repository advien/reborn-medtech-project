import pytest

from reborn.decision.confidence_gate import ConfidenceGate


def test_below_low_threshold_blocks_assist():
    gate = ConfidenceGate(low_threshold=0.4, high_threshold=0.7)
    result = gate.evaluate(0.2)
    assert result.allowed is False
    assert result.assist_scale == 0.0


def test_above_high_threshold_allows_full_assist():
    gate = ConfidenceGate(low_threshold=0.4, high_threshold=0.7)
    result = gate.evaluate(0.9)
    assert result.allowed is True
    assert result.assist_scale == 1.0


def test_between_thresholds_scales_linearly():
    gate = ConfidenceGate(low_threshold=0.4, high_threshold=0.8)
    result = gate.evaluate(0.6)
    assert result.allowed is True
    assert result.assist_scale == pytest.approx(0.5)


def test_invalid_thresholds_raise():
    with pytest.raises(ValueError):
        ConfidenceGate(low_threshold=0.8, high_threshold=0.4)
