import pytest
import time
from src.core.wallex_circuit_breaker import WallexCircuitBreaker

def test_stage29_circuit_breaker_normal_flow():
    cb = WallexCircuitBreaker(max_consecutive_errors=3, cooldown_seconds=10.0)
    assert cb.can_execute() is True
    
    cb.record_failure("HTTP 502 Bad Gateway")
    assert cb.can_execute() is True
    assert cb.failure_count == 1
    
    cb.record_success()
    assert cb.failure_count == 0
    assert cb.can_execute() is True

def test_stage29_circuit_breaker_trips_on_consecutive_errors():
    cb = WallexCircuitBreaker(max_consecutive_errors=2, cooldown_seconds=5.0)
    cb.record_failure("Timeout 1")
    assert cb.can_execute() is True
    
    cb.record_failure("Timeout 2")
    assert cb.is_open is True
    assert cb.can_execute() is False

def test_stage29_circuit_breaker_recovers_after_cooldown():
    cb = WallexCircuitBreaker(max_consecutive_errors=2, cooldown_seconds=0.1)
    cb.record_failure("Error 1")
    cb.record_failure("Error 2")
    assert cb.can_execute() is False
    
    time.sleep(0.15)
    assert cb.can_execute() is True
