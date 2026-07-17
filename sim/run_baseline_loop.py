"""Minimal 5-step Reborn control loop, running entirely against the sim HAL backend.

    1. Plant + variable-load stand-in       -> reborn.plant.elbow_model (placeholder)
    2. Actuator model with saturation       -> reborn.plant.actuator
    3. EMG frame player (synthetic here)    -> reborn.hal.sim_backend
    4. Deterministic state machine + gating -> reborn.decision
    5. Logging of every transition/event    -> reborn.logging.recorder

This is deliberately the smallest loop that exercises the full architecture end
to end (see docs/roadmap.md, "Reborn-стенд: порядок сборки"). The EMG signal is
synthetic and the plant is a placeholder — replace both with recorded datasets
(phase B) and real dynamics (phase C) without touching this wiring, since
everything here is expressed against reborn.hal interfaces.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from reborn.hal.interfaces import ActuatorCommand
from reborn.hal.sim_backend import SimActuatorSink, frames_from_emg_array
from reborn.decision.confidence_gate import ConfidenceGate
from reborn.decision.state_machine import StateMachine, SystemState
from reborn.logging.recorder import Recorder
from reborn.plant.actuator import ActuatorModel
from reborn.plant.elbow_model import ElbowModel
from reborn.safety.fault_detection import FaultDetector
from reborn.safety.fallback import FallbackMode, select_fallback
from reborn.safety.limits import SafetyLimits, enforce
from reborn.sensing.emg_qc import assess_quality
from reborn.sensing.features import extract_features

RAW_SAMPLE_RATE = 1000.0  # Hz, raw EMG sampling
FRAME_SIZE = 50  # raw samples per processing frame -> 20 Hz decision rate
N_FRAMES = 200  # 10 seconds of data
MAX_TORQUE = 2.0  # Nm, synthetic "fully confident assist" request


def synthetic_emg(n_frames: int, frame_size: int, raw_sample_rate: float) -> tuple[np.ndarray, np.ndarray]:
    """Alternating flex/rest bursts at `raw_sample_rate`, windowed into `n_frames`
    chunks of `frame_size` raw samples each, with one intentional dropout window.

    Quality/feature checks (reborn.sensing) need a window of samples to be
    meaningful (e.g. std over a window) — a single instantaneous value can't
    tell "dropout" from "quiet". Hence each SensorFrame here carries a short
    window, not one sample.
    """
    n_samples = n_frames * frame_size
    t = np.arange(n_samples) / raw_sample_rate
    envelope = 0.6 * (np.sin(2 * np.pi * 0.5 * t) > 0).astype(float)
    noise = 0.05 * np.random.default_rng(0).standard_normal(n_samples)
    raw = (envelope + noise).reshape(n_frames, frame_size)

    valid_mask = np.ones(n_frames, dtype=bool)
    dropout_frames = slice(75, 85)
    valid_mask[dropout_frames] = False
    raw[dropout_frames] = 0.0  # simulated flatline during dropout

    return raw, valid_mask


def main() -> None:
    emg, valid_mask = synthetic_emg(N_FRAMES, FRAME_SIZE, RAW_SAMPLE_RATE)
    decision_rate = RAW_SAMPLE_RATE / FRAME_SIZE
    sensor_source = list(frames_from_emg_array(emg, decision_rate, valid_mask=valid_mask))
    actuator_sink = SimActuatorSink()

    elbow = ElbowModel()
    actuator = ActuatorModel()
    fault_detector = FaultDetector()
    gate = ConfidenceGate()
    state_machine = StateMachine()
    limits = SafetyLimits()
    dt = 1.0 / decision_rate

    with Recorder("experiments/results/baseline_loop.jsonl") as recorder:
        for frame in sensor_source:
            channel = np.asarray(frame.emg).reshape(-1)
            quality = assess_quality(channel)
            features = extract_features(channel)

            confidence = min(1.0, features["rms"] / 0.4)
            intent = features["rms"] > 0.15

            fault = fault_detector.check_frame(frame_valid=frame.valid and quality.valid, latency_s=0.0)
            safety_ok = not fault.faulted

            previous_state = state_machine.state
            state = state_machine.step(intent=intent, confidence=confidence, safety_ok=safety_ok)
            if state != previous_state:
                recorder.record("state_transition", frm=previous_state.name, to=state.name)

            if fault.faulted:
                recorder.record("safety_event", reason=fault.reason, timestamp=frame.timestamp)

            fallback = select_fallback(faulted=fault.faulted, confidence=confidence)
            gate_result = gate.evaluate(confidence)

            if state in (SystemState.ASSIST, SystemState.DEGRADED) and gate_result.allowed and fallback == FallbackMode.NONE:
                requested_torque = MAX_TORQUE * gate_result.assist_scale
            elif fallback == FallbackMode.LIMITED_ASSIST:
                requested_torque = MAX_TORQUE * 0.2
            else:
                requested_torque = 0.0

            safe_torque = enforce(requested_torque, elbow.state.angle, elbow.state.velocity, limits)
            applied_torque = actuator.apply(safe_torque, dt)
            elbow.step(applied_torque, dt)

            actuator_sink.send(ActuatorCommand(timestamp=frame.timestamp, torque=applied_torque))

    print(f"Processed {len(sensor_source)} frames.")
    print(f"Final state: {state_machine.state.name}")
    print(f"Final elbow angle: {elbow.state.angle:.3f} rad")
    print(f"Commands recorded: {len(actuator_sink.history)}")
    print("Log written to experiments/results/baseline_loop.jsonl")


if __name__ == "__main__":
    main()
