"""Regression test for the sim loop's assist policy (CLAUDE.md invariant 3).

The audit found that a confidence of 0.39 requested more torque than a confidence
of 0.41: the limited-assist fallback acted as a floor below the gate's low
threshold. Assist must be a non-decreasing function of confidence.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

from reborn.decision.confidence_gate import ConfidenceGate
from reborn.decision.state_machine import StateMachine, SystemState
from reborn.safety.fallback import FallbackMode, select_fallback


def _load_sim_module():
    path = Path(__file__).resolve().parent.parent / "sim" / "run_baseline_loop.py"
    spec = importlib.util.spec_from_file_location("run_baseline_loop", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sim = _load_sim_module()


def _assist_for(confidence: float, *, intent: bool = True, safety_ok: bool = True) -> float:
    """One fresh tick of the decision layer, exactly as the sim loop combines it."""
    state = StateMachine().step(intent=intent, confidence=confidence, safety_ok=safety_ok)
    gate_result = ConfidenceGate().evaluate(confidence)
    fallback = select_fallback(faulted=not safety_ok, confidence=confidence)
    return sim.requested_assist_scale(state, gate_result, fallback)


def test_assist_is_non_decreasing_in_confidence():
    grid = np.linspace(0.0, 1.0, 201)
    scales = [_assist_for(float(c)) for c in grid]
    assert all(b >= a - 1e-12 for a, b in zip(scales, scales[1:]))


def test_the_audited_inversion_is_gone():
    assert _assist_for(0.39) <= _assist_for(0.41)
    assert _assist_for(0.39) == pytest.approx(0.0)


def test_limited_assist_is_a_cap_not_a_floor():
    gate_result = ConfidenceGate().evaluate(0.9)  # scale 1.0
    capped = sim.requested_assist_scale(SystemState.DEGRADED, gate_result, FallbackMode.LIMITED_ASSIST)
    assert capped == pytest.approx(sim.LIMITED_ASSIST_CAP)
    closed = ConfidenceGate().evaluate(0.1)
    assert sim.requested_assist_scale(SystemState.DEGRADED, closed, FallbackMode.LIMITED_ASSIST) == 0.0


def test_faults_and_inactive_states_request_nothing():
    open_gate = ConfidenceGate().evaluate(1.0)
    assert sim.requested_assist_scale(SystemState.ASSIST, open_gate, FallbackMode.PASSIVE) == 0.0
    for state in (SystemState.IDLE, SystemState.FALLBACK, SystemState.EMERGENCY_STOP):
        assert sim.requested_assist_scale(state, open_gate, FallbackMode.NONE) == 0.0
    assert _assist_for(0.95, safety_ok=False) == 0.0
