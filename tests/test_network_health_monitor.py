import pytest
import time
from src.core.network_health_monitor import NetworkHealthMonitor

def test_network_health_monitor_success():
    monitor = NetworkHealthMonitor(max_consecutive_failures=3, latency_threshold_ms=1000.0)
    monitor.record_success(120.0)
    monitor.record_success(130.0)
    status = monitor.get_status()
    assert status.is_healthy is True
    assert status.consecutive_failures == 0
    assert status.avg_latency_ms == 125.0
    assert status.is_circuit_broken is False
    assert monitor.is_operation_permitted() is True

def test_network_health_monitor_circuit_break():
    monitor = NetworkHealthMonitor(
        max_consecutive_failures=2,
        circuit_cooldown_seconds=1.0
    )
    monitor.record_failure("DNS Resolution Error")
    assert monitor.is_operation_permitted() is True
    
    monitor.record_failure("Connection Timeout")
    assert monitor.is_operation_permitted() is False
    status = monitor.get_status()
    assert status.is_healthy is False
    assert status.is_circuit_broken is True
    assert status.consecutive_failures == 2
    assert status.last_error == "Connection Timeout"

    # Wait for cooldown to expire
    time.sleep(1.05)
    assert monitor.is_operation_permitted() is True
