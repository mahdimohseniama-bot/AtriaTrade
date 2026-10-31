import pytest
import time
from src.core.wallex_rate_limiter import WallexRateLimiter

def test_stage34_rate_limiter_allows_burst():
    limiter = WallexRateLimiter(max_requests_per_minute=60, burst_limit=3)
    
    # 3 bursts should succeed immediately
    assert limiter.acquire(1.0) is True
    assert limiter.acquire(1.0) is True
    assert limiter.acquire(1.0) is True
    
    # 4th burst exceeds bucket limit
    assert limiter.acquire(1.0) is False

def test_stage34_rate_limiter_token_refill():
    limiter = WallexRateLimiter(max_requests_per_minute=60, burst_limit=1)
    
    assert limiter.acquire(1.0) is True
    assert limiter.acquire(1.0) is False
    
    # Simulate time passing for refill
    limiter.last_update -= 1.5  # 1.5 seconds ago
    assert limiter.acquire(1.0) is True

def test_stage34_rate_limiter_handles_429_backoff():
    limiter = WallexRateLimiter(max_requests_per_minute=60, burst_limit=5)
    
    # First 429
    res1 = limiter.handle_response_code(429)
    assert res1["throttled"] is True
    assert res1["backoff_seconds"] == 3.0
    assert limiter.tokens == 0.0
    
    # Second consecutive 429 escalates backoff
    res2 = limiter.handle_response_code(429)
    assert res2["throttled"] is True
    assert res2["backoff_seconds"] == 6.0
    
    # Normal response resets counter
    res3 = limiter.handle_response_code(200)
    assert res3["throttled"] is False
    assert res3["backoff_seconds"] == 0.0
    assert limiter.consecutive_429 == 0
