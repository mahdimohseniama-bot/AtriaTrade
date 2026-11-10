import pytest
from src.core.network_health_monitor import NetworkHealthMonitor
from src.core.safe_exchange_caller import SafeExchangeCaller

def test_safe_exchange_caller_success():
    monitor = NetworkHealthMonitor(max_consecutive_failures=2)
    caller = SafeExchangeCaller(monitor)

    dummy_fetch = lambda pair: {"pair": pair, "bid": 100000.0}
    ok, result, err = caller.execute("fetch_ticker", dummy_fetch, "BTCIRT")

    assert ok is True
    assert result == {"pair": "BTCIRT", "bid": 100000.0}
    assert err is None
    assert monitor.get_status().is_healthy is True

def test_safe_exchange_caller_failure_and_circuit_tripping():
    monitor = NetworkHealthMonitor(max_consecutive_failures=2, circuit_cooldown_seconds=10.0)
    caller = SafeExchangeCaller(monitor)

    def failing_api():
        raise ConnectionResetError("Connection lost to Wallex endpoint")

    # First failure
    ok1, res1, err1 = caller.execute("fetch_orderbook", failing_api)
    assert ok1 is False
    assert res1 is None
    assert "Connection lost" in err1
    assert monitor.is_operation_permitted() is True

    # Second failure triggers circuit breaker
    ok2, res2, err2 = caller.execute("fetch_orderbook", failing_api)
    assert ok2 is False
    assert monitor.is_operation_permitted() is False

    # Third call is blocked immediately without executing failing_api
    ok3, res3, err3 = caller.execute("fetch_orderbook", failing_api)
    assert ok3 is False
    assert "Network circuit breaker is active" in err3
