import pytest
from unittest.mock import Mock
from src.core.network_health_monitor import NetworkHealthMonitor
from src.adapters.wallex_resilient_session import WallexResilientSession

def test_session_success_on_first_try():
    monitor = NetworkHealthMonitor()
    session = WallexResilientSession(network_monitor=monitor, max_retries=3, backoff_factor=0.01)
    
    mock_api = Mock(return_value={"symbol": "BTCIRT", "price": "6000000000"})
    response = session.request_with_retry("get_ticker", mock_api)
    
    assert response["success"] is True
    assert response["attempts"] == 1
    assert response["data"]["price"] == "6000000000"
    assert response["error"] is None
    assert mock_api.call_count == 1

def test_session_recovers_after_transient_failure():
    monitor = NetworkHealthMonitor(max_consecutive_failures=5)
    session = WallexResilientSession(network_monitor=monitor, max_retries=3, backoff_factor=0.01)
    
    mock_api = Mock(side_effect=[
        ConnectionResetError("Temporary drop"),
        {"symbol": "BTCIRT", "price": "6100000000"}
    ])
    
    response = session.request_with_retry("get_ticker", mock_api)
    assert response["success"] is True
    assert response["attempts"] == 2
    assert response["data"]["price"] == "6100000000"
    assert mock_api.call_count == 2

def test_session_stops_immediately_when_circuit_tripped():
    # max_consecutive_failures = 1 forces circuit breaker open on first failure
    monitor = NetworkHealthMonitor(max_consecutive_failures=1, circuit_cooldown_seconds=10.0)
    session = WallexResilientSession(network_monitor=monitor, max_retries=5, backoff_factor=0.01)

    mock_api = Mock(side_effect=TimeoutError("Wallex gateway timeout"))
    response = session.request_with_retry("get_orderbook", mock_api)

    assert response["success"] is False
    assert response["attempts"] == 1
    assert "Wallex gateway timeout" in response["error"]
    assert mock_api.call_count == 1
