from reborn.decision.state_machine import StateMachine, SystemState


def test_starts_idle():
    sm = StateMachine()
    assert sm.state == SystemState.IDLE


def test_high_confidence_intent_moves_to_assist():
    sm = StateMachine()
    state = sm.step(intent=True, confidence=0.9, safety_ok=True)
    assert state == SystemState.ASSIST


def test_moderate_confidence_intent_moves_to_degraded():
    sm = StateMachine()
    state = sm.step(intent=True, confidence=0.5, safety_ok=True)
    assert state == SystemState.DEGRADED


def test_low_confidence_or_no_intent_stays_idle():
    sm = StateMachine()
    assert sm.step(intent=True, confidence=0.1, safety_ok=True) == SystemState.IDLE
    assert sm.step(intent=False, confidence=0.9, safety_ok=True) == SystemState.IDLE


def test_safety_not_ok_forces_fallback_regardless_of_confidence():
    sm = StateMachine()
    sm.step(intent=True, confidence=0.9, safety_ok=True)
    state = sm.step(intent=True, confidence=0.9, safety_ok=False)
    assert state == SystemState.FALLBACK


def test_fallback_is_sticky_until_reset():
    sm = StateMachine()
    sm.step(intent=True, confidence=0.9, safety_ok=False)
    assert sm.state == SystemState.FALLBACK
    # Even a perfect subsequent tick must not un-stick FALLBACK on its own.
    state = sm.step(intent=True, confidence=1.0, safety_ok=True)
    assert state == SystemState.FALLBACK

    sm.reset()
    assert sm.state == SystemState.IDLE


def test_emergency_overrides_everything_and_is_sticky():
    sm = StateMachine()
    sm.step(intent=True, confidence=0.9, safety_ok=True)
    state = sm.step(intent=True, confidence=0.9, safety_ok=True, emergency=True)
    assert state == SystemState.EMERGENCY_STOP

    # Stays in emergency stop even with a subsequent clean tick.
    state = sm.step(intent=True, confidence=0.9, safety_ok=True)
    assert state == SystemState.EMERGENCY_STOP

    sm.reset()
    assert sm.state == SystemState.IDLE
