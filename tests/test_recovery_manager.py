"""
Tests for RecoveryManager - AtriaTrade
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.recovery_manager import RecoveryManager


def test_initialization():
    manager = RecoveryManager()

    assert manager.mode == "paper"
    assert manager.max_drawdown_pct == 20.0
    assert manager.recovery_active is False
    assert manager.emergency_stop is False
    assert manager.get_status()["real_trading_enabled"] is False

    print("PASS: test_initialization")


def test_normal_drawdown():
    manager = RecoveryManager(max_drawdown_pct=20.0)

    result = manager.evaluate(5.0)

    assert result["status"] == "normal"
    assert result["action"] == "no_recovery_action"
    assert result["order_submitted"] is False
    assert manager.recovery_active is False

    print("PASS: test_normal_drawdown")


def test_critical_drawdown():
    manager = RecoveryManager(max_drawdown_pct=20.0)

    result = manager.evaluate(20.0)

    assert result["status"] == "critical"
    assert result["action"] == "reduce_risk_and_pause_entries"
    assert result["recovery_active"] is True
    assert result["order_submitted"] is False

    print("PASS: test_critical_drawdown")


def test_recovery_completion():
    manager = RecoveryManager(
        max_drawdown_pct=20.0,
        recovery_target_pct=5.0,
    )

    critical = manager.evaluate(25.0)
    assert critical["status"] == "critical"
    assert manager.recovery_active is True

    recovered = manager.evaluate(4.0)

    assert recovered["status"] == "recovered"
    assert recovered["action"] == "resume_with_normal_risk"
    assert manager.recovery_active is False

    print("PASS: test_recovery_completion")


def test_emergency_stop():
    manager = RecoveryManager()

    event = manager.activate_emergency_stop("Test safety stop")

    assert event["event"] == "emergency_stop_activated"
    assert event["order_submitted"] is False
    assert manager.emergency_stop is True

    result = manager.evaluate(1.0)

    assert result["status"] == "emergency_stop"
    assert result["action"] == "halt_simulation"
    assert result["order_submitted"] is False

    reset_event = manager.reset_emergency_stop()

    assert reset_event["event"] == "emergency_stop_reset"
    assert manager.emergency_stop is False

    print("PASS: test_emergency_stop")


def test_cycle_and_cooldown():
    manager = RecoveryManager(
        max_drawdown_pct=10.0,
        recovery_target_pct=2.0,
        cooldown_cycles=3,
    )

    manager.evaluate(12.0)

    manager.advance_cycle(1)
    result = manager.evaluate(5.0)

    # Recovery remains active while drawdown is above target.
    assert result["status"] == "recovering"

    manager.evaluate(1.0)
    assert manager.recovery_active is False

    print("PASS: test_cycle_and_cooldown")


def test_invalid_values():
    invalid_cases = [
        {"max_drawdown_pct": 0},
        {"max_drawdown_pct": 101},
        {"max_drawdown_pct": 20, "recovery_target_pct": 20},
        {"cooldown_cycles": -1},
        {"mode": "live"},
    ]

    for kwargs in invalid_cases:
        try:
            RecoveryManager(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected ValueError for {kwargs}")

    print("PASS: test_invalid_values")


if __name__ == "__main__":
    print("START: RecoveryManager Tests")

    test_initialization()
    test_normal_drawdown()
    test_critical_drawdown()
    test_recovery_completion()
    test_emergency_stop()
    test_cycle_and_cooldown()
    test_invalid_values()

    print("ALL RecoveryManager TESTS PASSED SUCCESSFULLY!")
