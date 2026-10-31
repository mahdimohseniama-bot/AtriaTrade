import pytest
from unittest.mock import MagicMock
from src.core.wallex_heartbeat import WallexHeartbeatMonitor

@pytest.fixture
def mock_adapter():
    adapter = MagicMock()
    adapter.ping.return_value = True
    return adapter

def test_stage33_heartbeat_healthy(mock_adapter):
    monitor = WallexHeartbeatMonitor(mock_adapter, max_latency_ms=500.0, max_consecutive_drops=3)
    res = monitor.ping()
    
    assert res["is_healthy"] is True
    assert res["reason"] == "normal"
    assert res["consecutive_drops"] == 0
    assert not monitor.should_pause_trading()

def test_stage33_heartbeat_high_latency(mock_adapter):
    # Set threshold very low to trigger high latency
    monitor = WallexHeartbeatMonitor(mock_adapter, max_latency_ms=0.00001, max_consecutive_drops=2)
    res = monitor.ping()
    
    assert res["is_healthy"] is False
    assert res["reason"] == "high_latency"
    assert res["consecutive_drops"] == 1
    assert not monitor.should_pause_trading()
    
    # Second failure triggers trading pause threshold
    monitor.ping()
    assert monitor.should_pause_trading()

def test_stage33_heartbeat_exception_handling(mock_adapter):
    mock_adapter.ping.side_effect = ConnectionError("Network dropped")
    monitor = WallexHeartbeatMonitor(mock_adapter, max_latency_ms=500.0, max_consecutive_drops=2)
    
    res = monitor.ping()
    assert res["is_healthy"] is False
    assert "exception" in res["reason"]
    assert monitor.consecutive_drops == 1
    
    # Recovery check
    mock_adapter.ping.side_effect = None
    mock_adapter.ping.return_value = True
    recovery_res = monitor.ping()
    assert recovery_res["is_healthy"] is True
    assert monitor.consecutive_drops == 0
