from reborn.safety.limits import SafetyLimits, check_angle, check_velocity, clamp_torque, enforce


def test_clamp_torque_within_limits_is_unchanged():
    limits = SafetyLimits(max_torque=5.0)
    assert clamp_torque(3.0, limits) == 3.0
    assert clamp_torque(-3.0, limits) == -3.0


def test_clamp_torque_saturates_at_limits():
    limits = SafetyLimits(max_torque=5.0)
    assert clamp_torque(10.0, limits) == 5.0
    assert clamp_torque(-10.0, limits) == -5.0


def test_check_angle_bounds():
    limits = SafetyLimits(min_angle=0.0, max_angle=2.0)
    assert check_angle(1.0, limits) is True
    assert check_angle(-0.1, limits) is False
    assert check_angle(2.1, limits) is False


def test_check_velocity_bounds():
    limits = SafetyLimits(max_velocity=3.0)
    assert check_velocity(2.9, limits) is True
    assert check_velocity(-2.9, limits) is True
    assert check_velocity(3.1, limits) is False


def test_enforce_clamps_torque_when_state_is_safe():
    limits = SafetyLimits(max_torque=5.0, min_angle=0.0, max_angle=2.0, max_velocity=3.0)
    assert enforce(10.0, angle=1.0, velocity=1.0, limits=limits) == 5.0


def test_enforce_zeroes_torque_when_angle_out_of_bounds():
    limits = SafetyLimits(max_torque=5.0, min_angle=0.0, max_angle=2.0, max_velocity=3.0)
    assert enforce(3.0, angle=2.5, velocity=0.0, limits=limits) == 0.0


def test_enforce_zeroes_torque_when_velocity_out_of_bounds():
    limits = SafetyLimits(max_torque=5.0, min_angle=0.0, max_angle=2.0, max_velocity=3.0)
    assert enforce(3.0, angle=1.0, velocity=5.0, limits=limits) == 0.0
