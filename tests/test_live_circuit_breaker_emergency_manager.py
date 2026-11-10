import pytest
from unittest.mock import Mock
from src.core.live_circuit_breaker_emergency_manager import LiveCircuitBreakerEmergencyManager

def test_consecutive_errors_trigger_halt():
    manager = LiveCircuitBreakerEmergencyManager(max_consecutive_errors=3)
    assert manager.can_trade()["permitted"] is True

    manager.record_error("NETWORK_TIMEOUT")
    assert manager.can_trade()["permitted"] is True
    assert manager.consecutive_errors == 1

    manager.record_error("REJECTED_ORDER")
    assert manager.can_trade()["permitted"] is True
    assert manager.consecutive_errors == 2

    # Third error trips the breaker
    tripped = manager.record_error("API_KEY_INVALID")
    assert tripped is True
    assert manager.can_trade()["permitted"] is False
    assert "EXCESSIVE_CONSECUTIVE_ERRORS" in manager.can_trade()["reason"]

def test_drawdown_triggers_emergency_halt():
    manager = LiveCircuitBreakerEmergencyManager(max_daily_loss_pct=0.05) # 5%
    # 100M down to 94M -> 6% drawdown
    tripped = manager.evaluate_daily_drawdown(starting_balance=100000000.0, current_balance=94000000.0)
    assert tripped is True
    assert manager.can_trade()["permitted"] is False
    assert "MAX_DAILY_DRAWDOWN_EXCEEDED" in manager.can_trade()["reason"]

def test_trigger_emergency_halt_executes_cancel():
    manager = LiveCircuitBreakerEmergencyManager()
    mock_cancel_all = Mock()

    res = manager.trigger_emergency_halt(reason="PANIC_BUTTON", cancel_all_func=mock_cancel_all)
    assert res["halted"] is True
    assert res["orders_cancelled"] is True
    mock_cancel_all.assert_called_once()
    assert manager.can_trade()["permitted"] is False

def test_reset_clears_state():
    manager = LiveCircuitBreakerEmergencyManager()
    manager.trigger_emergency_halt("TEST_HALT")
    assert manager.can_trade()["permitted"] is False

    manager.reset()
    assert manager.can_trade()["permitted"] is True
    assert manager.consecutive_errors == 0
