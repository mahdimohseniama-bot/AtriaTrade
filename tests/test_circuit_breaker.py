import pytest
from datetime import datetime, timezone, timedelta
from src.core.circuit_breaker import CircuitBreaker


def test_circuit_breaker_initial_state():
    cb = CircuitBreaker()
    assert not cb.is_halted
    assert cb.halt_reason is None
    status = cb.get_status()
    assert status["is_halted"] is False
    assert status["consecutive_failures"] == 0


def test_consecutive_failures_trigger_halt():
    cb = CircuitBreaker(max_consecutive_failures=2)
    cb.record_execution_result(False, "API Timeout")
    assert not cb.is_halted

    cb.record_execution_result(False, "Connection Refused")
    assert cb.is_halted
    assert "Consecutive execution failures exceeded" in cb.halt_reason


def test_successful_execution_resets_failure_counter():
    cb = CircuitBreaker(max_consecutive_failures=3)
    cb.record_execution_result(False, "Error 1")
    cb.record_execution_result(False, "Error 2")
    assert cb.get_status()["consecutive_failures"] == 2

    cb.record_execution_result(True)
    assert cb.get_status()["consecutive_failures"] == 0
    assert not cb.is_halted


def test_extreme_volatility_triggers_halt():
    cb = CircuitBreaker(volatility_threshold_pct=0.05)
    is_safe = cb.evaluate_market_conditions(price_change_pct=0.06, current_drawdown_pct=0.01)
    assert not is_safe
    assert cb.is_halted
    assert "Extreme market volatility" in cb.halt_reason


def test_drawdown_limit_triggers_halt():
    cb = CircuitBreaker(max_drawdown_pct_halt=0.04)
    is_safe = cb.evaluate_market_conditions(price_change_pct=0.01, current_drawdown_pct=0.05)
    assert not is_safe
    assert cb.is_halted
    assert "Emergency drawdown limit hit" in cb.halt_reason


def test_manual_reset():
    cb = CircuitBreaker()
    cb.evaluate_market_conditions(price_change_pct=0.10, current_drawdown_pct=0.0)
    assert cb.is_halted

    cb.reset(manual=True)
    assert not cb.is_halted
    assert cb.halt_reason is None
    assert cb.get_status()["consecutive_failures"] == 0


def test_invalid_parameters():
    with pytest.raises(ValueError, match="max_consecutive_failures"):
        CircuitBreaker(max_consecutive_failures=0)

    with pytest.raises(ValueError, match="max_drawdown_pct_halt"):
        CircuitBreaker(max_drawdown_pct_halt=-0.01)
